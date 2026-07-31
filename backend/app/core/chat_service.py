from google import genai
from dotenv import load_dotenv
import os
from app.core.neo4j_tool import execute_neo4j_query
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

neo4j_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="execute_neo4j_query",
            description="Executes a Cypher query on the Neo4j medical knowledge graph and returns the matching results.",
            parameters={
                "type": "object",
                "properties": {
                    "cypher_query": {
                        "type": "string",
                        "description": "The Cypher query to execute."
                    }
                },
                "required": ["cypher_query"],
            },
        )
    ]
)



def chat(model: str, messages: list):

    prompt = "\n".join(
        [message["content"] for message in messages]
    )

    return client.models.generate_content_stream(
        model=model,
        contents=prompt,
    )

def get_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "gemini-3.6-flash",
                "object": "model",
                "owned_by": "google"
            }
        ]
    }