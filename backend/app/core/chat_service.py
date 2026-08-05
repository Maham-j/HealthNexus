from groq import Groq
from dotenv import load_dotenv
from app.core.neo4j_tool import execute_neo4j_query, neo4j_tool_groq
from app.core.rag_tool import rag_tool_groq, get_rag_tool

import os
import json
import time
import pprint


load_dotenv()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def should_use_neo4j_tool(messages):
    if not messages:
        return False

    prompt = messages[-1].get("content", "")
    prompt_lower = prompt.lower()

    metadata_patterns = [
        "### task:",
        "generate a concise",
        "generate 1-3 broad tags",
        "suggest 3-5 relevant follow-up questions",
    ]
    if any(pattern in prompt_lower for pattern in metadata_patterns):
        return False

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Reply with exactly one word: YES if the message is a biomedical "
                        "or medical question (including diseases, symptoms, treatments, genes, "
                        "drugs, drug interactions, lifestyle/management of a condition, or risk "
                        "factors). Reply NO if it is casual conversation or unrelated to health."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        answer = resp.choices[0].message.content.strip().upper()
        return answer.startswith("Y")
    except Exception as e:
        print("ROUTER CALL FAILED:", e)
        return False

def chat(model: str, messages: list):
    print("MODEL RECEIVED:", model)

    if not (model.startswith("llama") or model.startswith("openai/gpt-oss")):
        return {"text": "Unsupported model.", "tool_call": False}

    print("USING GROQ")
    start = time.time()

    system_prompt = {
        "role": "system",
        "content": """
    You are a biomedical assistant connected to a Neo4j medical knowledge graph.

    For biomedical questions follow this workflow:

    1. Use fetchSimilarQueries only when you need help generating a Cypher query.
    2. After getting examples, always call execute_neo4j_query.
    3. Never use fetchSimilarQueries output as medical evidence.
    4. Only execute_neo4j_query results can be used to answer the user.
    5. Never use FAISS findings as the final answer.
    6. FAISS is only a query-generation helper.

    General rules:

    7. Do not answer biomedical questions from your own knowledge.
    8. The Neo4j knowledge graph is the only source of truth for medical information.
    9. After receiving execute_neo4j_query results, explain the answer using only those retrieved results.
    10. If Neo4j does not contain relevant information, clearly say that the information is not available in the knowledge graph.
    11. For casual conversation (greetings, small talk), answer normally without using tools.
    """
    }

    if not should_use_neo4j_tool(messages):
        print("NO NEO4J TOOL")
        try:
            resp = groq_client.chat.completions.create(
                model=model,
                messages=[system_prompt] + messages,
            )
        except Exception as e:
            print("CHAT CALL FAILED:", e)
            return {"text": "I had trouble processing that — could you try again?", "tool_call": False}

        text = resp.choices[0].message.content
        if not text or not text.strip():
            print("EMPTY RESPONSE FROM MODEL")
            return {"text": "I'm not sure how to answer that — could you rephrase?", "tool_call": False}
        return {"text": text, "tool_call": False}
    
    print("USING MEDICAL TOOLS")

    
    # ---------- Turn 1: force fetchSimilarQueries ----------
    try:
        resp1 = groq_client.chat.completions.create(
            model=model,
            messages=[system_prompt] + messages,
            tools=[rag_tool_groq],
            tool_choice={"type": "function", "function": {"name": "fetchSimilarQueries"}},
        )
        rag_call = resp1.choices[0].message.tool_calls[0]
    except Exception as e:
        print("RAG TOOL CALL FAILED:", e)
        return {"text": "I had trouble processing that question — could you rephrase it?", "tool_call": False}


    
    rag_args = json.loads(rag_call.function.arguments)
    query = rag_args["query"]
    print("FETCHING SIMILAR QUERIES:", query)

    rag_results = get_rag_tool().fetch_similar_queries(query)
    examples = [{"question": r["question"], "cypher": r["cypher"]} for r in rag_results]
    print("RAG EXAMPLES:", examples)

    # ---------- Turn 2: force execute_neo4j_query, now informed by examples ----------
    cypher_messages = [system_prompt] + messages + [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": rag_call.id,
                    "type": "function",
                    "function": {
                        "name": "fetchSimilarQueries",
                        "arguments": rag_call.function.arguments,
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": rag_call.id,
            "content": json.dumps(examples),
        },
    ]

    try:
        resp2 = groq_client.chat.completions.create(
            model=model,
            messages=cypher_messages,
            tools=[neo4j_tool_groq],
            tool_choice={"type": "function", "function": {"name": "execute_neo4j_query"}},
        )
        cypher_call = resp2.choices[0].message.tool_calls[0]
    except Exception as e:
        print("CYPHER GENERATION FAILED:", e)
        return {"text": "I had trouble generating a query for that question — could you rephrase it?", "tool_call": False}

    
    cypher_args = json.loads(cypher_call.function.arguments)
    cypher = cypher_args["cypher_query"]
    print("EXECUTING CYPHER:", cypher)

    try:
        results = execute_neo4j_query(cypher)
    except Exception as e:
        print("NEO4J EXECUTION ERROR:", e)
        return {
            "text": "The knowledge graph does not contain enough information.",
            "tool_call": True,
            "results": [],
        }

    print("RESULTS:", results)

    # ---------- Short-circuit on empty results ----------
    if not results:
        return {
            "text": "The knowledge graph does not contain enough information.",
            "tool_call": True,
            "results": [],
        }

    # ---------- Turn 3: final grounded answer ----------
    follow_up_messages = [
        {
            "role": "system",
            "content": """
                You are given the output of a Neo4j query.
                Use ONLY the information contained in the tool output.
                Do NOT use your own medical knowledge.

                The tool output contains only factual associations (e.g., "exposure X is linked to disease Y").
                It does NOT contain instructions, remediation methods, product recommendations, or any
                guidance on HOW to avoid, treat, or manage anything.

                You may state which items are associated with the condition, exactly as returned.
                You must NOT invent HOW to avoid, reduce, or manage exposure to any item — no cleaning
                tips, no protective equipment suggestions, no dietary substitutions, no "practical steps."
                Example of what NOT to do: turning "Dust is linked to asthma" into "use a HEPA vacuum."
                Example of what TO do: "The knowledge graph lists Dust as an exposure associated with
                asthma. It does not provide guidance on how to reduce dust exposure."

                Do NOT infer or add diseases, genes, explanations, or relationships not present in the data.
                If the tool output is insufficient, say "The knowledge graph does not contain enough information."
                .....
                Present the answer as flowing prose in paragraph form, not as a bulleted or numbered list,
                unless the user explicitly asks for a list.
                """,
        }
    ] + messages + [
        {"role": "user", "content": f"Neo4j results:\n{json.dumps(results)}"},
    ]

    try:
        follow_up = groq_client.chat.completions.create(
            model=model,
            messages=follow_up_messages,
            temperature=0,
            tool_choice="none",
        )
        final_text = follow_up.choices[0].message.content
    except Exception as e:
        print("CYPHER GENERATION FAILED:", e)
        if "429" in str(e) or "rate_limit" in str(e).lower():
            return {"text": "The service has reached its usage limit for now — please try again later.", "tool_call": False}
        return {"text": "I had trouble generating a query for that question — could you rephrase it?", "tool_call": False}
        
    print("FINAL ANSWER:", final_text)
    print(f"Total time: {time.time() - start:.2f}s")

    return {"text": final_text, "tool_call": True, "results": results}
            

def get_models():
    print("GETTING MODELS")
    return {
        "object": "list",
        "data": [
    
            {
                "id": "llama-3.3-70b-versatile",
                "object": "model",
                "owned_by": "groq"
            },
            {
                "id": "openai/gpt-oss-120b",
                "object": "model",
                "owned_by": "groq"
            }

        ]
    }