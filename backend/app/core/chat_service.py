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
    """
    Return True only for biomedical questions.
    Skip OpenWebUI metadata requests and general chat.
    """
    if not messages:
        return False

    prompt = messages[-1].get("content", "").lower()
    # OpenWebUI internal requests
    metadata_patterns = [
        "### task:",
        "generate a concise",
        "generate 1-3 broad tags",
        "suggest 3-5 relevant follow-up questions",
    ]

    if any(pattern in prompt for pattern in metadata_patterns):
        return False

    medical_keywords = [
        "disease", "protein", "gene", "drug", "medicine",
        "symptom", "treatment", "diagnosis", "therapy",
        "cancer", "asthma", "diabetes", "covid",
        "patient", "virus", "bacteria", "infection",
        "heart", "lung", "kidney", "brain"
    ]

    return any(keyword in prompt for keyword in medical_keywords)

def chat(model: str, messages: list):
    print("MODEL RECEIVED:", model)

    if not model.startswith("llama"):
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
        resp = groq_client.chat.completions.create(
            model=model,
            messages=[system_prompt] + messages,
        )
        return {"text": resp.choices[0].message.content, "tool_call": False}

    print("USING MEDICAL TOOLS")

    # ---------- Turn 1: force fetchSimilarQueries ----------
    resp1 = groq_client.chat.completions.create(
        model=model,
        messages=[system_prompt] + messages,
        tools=[rag_tool_groq],
        tool_choice={"type": "function", "function": {"name": "fetchSimilarQueries"}},
    )
    rag_call = resp1.choices[0].message.tool_calls[0]
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

    resp2 = groq_client.chat.completions.create(
        model=model,
        messages=cypher_messages,
        tools=[neo4j_tool_groq],
        tool_choice={"type": "function", "function": {"name": "execute_neo4j_query"}},
    )
    cypher_call = resp2.choices[0].message.tool_calls[0]
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
            Do NOT infer or add diseases, genes, explanations, or relationships not present in the data.
            If the tool output is insufficient, say "The knowledge graph does not contain enough information."
            """,
        }
    ] + messages + [
        {"role": "user", "content": f"Neo4j results:\n{json.dumps(results)}"},
    ]

    follow_up = groq_client.chat.completions.create(
        model=model,
        messages=follow_up_messages,
        temperature=0,
        tool_choice="none",
    )
    final_text = follow_up.choices[0].message.content
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
            }

        ]
    }