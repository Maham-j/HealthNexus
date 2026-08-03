from groq import Groq
from dotenv import load_dotenv
from app.core.neo4j_tool import execute_neo4j_query, neo4j_tool_groq

import os
import json
import time


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

    # ---------- Groq ----------
    if model.startswith("llama"):
        print("USING GROQ")

        start = time.time()
        system_prompt = {
                "role": "system",
                "content": """
            You are a biomedical assistant connected to a Neo4j medical knowledge graph.

            Rules:
            1. For any biomedical question related to diseases, genes, proteins, drugs,
            symptoms, treatments, diagnosis, or medical conditions, always use the Neo4j tool.

            2. Do not answer biomedical questions from your own knowledge.

            3. The Neo4j knowledge graph is the only source of truth for medical information.

            4. After receiving Neo4j results, explain the answer using only the retrieved information.

            5. If Neo4j does not contain relevant information, clearly tell the user that
            the information is not available in the knowledge graph.

            6. For casual conversation (greetings, small talk), answer normally without using tools.
            """
            }
        request = {
        "model": model,
        "messages": [system_prompt] + messages,
    }

        print("SHOULD USE NEO4J:", should_use_neo4j_tool(messages))
        if should_use_neo4j_tool(messages):
            print("USING NEO4J TOOL")
            request["tools"] = [neo4j_tool_groq]
            request["tool_choice"] = {
            "type": "function",
            "function": {
                "name": "execute_neo4j_query"
            }
        }
        else:
            print("NO NEO4J TOOL")

        # First LLM call

        response = groq_client.chat.completions.create(**request)
        print(f"Groq call took {time.time() - start:.2f}s")


        message = response.choices[0].message
        print("CONTENT:", message.content)
        print("TOOL CALLS:", message.tool_calls)
        
        if not message.content and not message.tool_calls:
            return {
                "text": "I couldn't generate a response.",
                "tool_call": False,
            }


        # Avoid sending empty database results back to the LLM
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            cypher = arguments["cypher_query"]

            print("EXECUTING CYPHER:", cypher)

            results = execute_neo4j_query(cypher)
            print("RESULTS:", results)

            if not results:
                results = []
                    

            # Send results back to Groq for a real final answer
            follow_up_messages = messages + [
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": "execute_neo4j_query",
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(results),
                },
            ]

            follow_up = groq_client.chat.completions.create(
                model=model,
                messages=follow_up_messages,
                tools=[neo4j_tool_groq],
            )

            final_text = follow_up.choices[0].message.content
            print("FINAL ANSWER:", final_text)

            return {
                "text": final_text,
                "tool_call": True,
                "results": results,
            }

        # Normal response (no tool call)
        return {
            "text": message.content,
            "tool_call": False,
        }
            

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