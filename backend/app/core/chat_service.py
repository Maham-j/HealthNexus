from email.mime import message
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


def chat(model: str, messages: list):
    print("MODEL RECEIVED:", model)

    # ---------- Groq ----------
    if model.startswith("llama"):
        print("USING GROQ")

        start = time.time()
        response = groq_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[neo4j_tool_groq],
            tool_choice="auto",
        )
        print(f"Groq call took {time.time() - start:.2f}s")

        message = response.choices[0].message
        print("CONTENT:", message.content)
        print("TOOL CALLS:", message.tool_calls)

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            cypher = arguments["cypher_query"]

            print("EXECUTING CYPHER:", cypher)
            results = execute_neo4j_query(cypher)
            print("RESULTS:", results)

            

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