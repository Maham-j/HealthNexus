from email.mime import message
from groq import Groq
from dotenv import load_dotenv
import os
import json
from app.core.neo4j_tool import execute_neo4j_query
import time


load_dotenv()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ---------- Groq: plain dict, OpenAI-style function calling ----------
neo4j_tool_groq = {
    "type": "function",
    "function": {
        "name": "execute_neo4j_query",
        "description": """
                Use this tool whenever the user asks about information stored in the medical knowledge graph, PrimeKG, Neo4j, diseases, drugs, proteins, pathways, or biomedical relationships. 
                Do not answer from memory if the user explicitly asks to use the graph.
                Execute Cypher queries against the PrimeKG medical knowledge graph.

                Database schema:

                Node label:
                - Entity

                Node properties:
                - node_name
                - node_type
                - node_id
                - node_source
                - node_index

                Possible node types:
                - disease
                - drug
                - gene/protein
                - effect/phenotype
                - pathway
                - exposure
                - biological_process
                - molecular_function
                - cellular_component

                Relationship types include:
                - protein_protein
                - drug_protein
                - contraindication
                - indication
                - off-label use
                - drug_drug
                - phenotype_protein
                - phenotype_phenotype
                - disease_phenotype_negative
                - disease_phenotype_positive
                - disease_protein
                - disease_disease
                - drug_effect
                - bioprocess_bioprocess
                - molfunc_molfunc
                - cellcomp_cellcomp
                - molfunc_protein
                - cellcomp_protein
                - bioprocess_protein
                Always use:
                MATCH (n:Entity)

                Filter diseases using:
                WHERE n.node_type = 'disease'

                Search names using:
                n.node_name

                Never use labels like Disease or relationships like RELATED_TO.
                """
        ,           
        "parameters": {
            "type": "object",
            "properties": {
                "cypher_query": {
                    "type": "string",
                    "description": "Cypher query to execute"
                }
            },
            "required": ["cypher_query"]
        }
    }
}


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
            
# def chat(model: str, messages: list):

#     prompt = "\n".join(
#         [message["content"] for message in messages]
#     )

#     return client.models.generate_content_stream(
#     model=model,
#     contents=prompt,
#     config=types.GenerateContentConfig(
#         tools=[neo4j_tool],
#     ),
# )

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