"""Defines the Neo4j tool, dynamically builds its schema description,
and executes Cypher queries against the Neo4j database.
"""
from app.core.neo4j_connector import neo4j_connector
import time


def get_node_types():
    query = """
    MATCH (n:Entity)
    RETURN DISTINCT n.node_type AS node_type
    ORDER BY node_type
    """
    result = neo4j_connector.run_query(query)
    return [r["node_type"] for r in result]


def get_node_properties():
    query = """
    MATCH (n:Entity)
    RETURN keys(n) AS properties
    LIMIT 1
    """
    result = neo4j_connector.run_query(query)
    return result[0]["properties"]


def get_relationship_types():
    query = """
    MATCH ()-[r]->()
    RETURN DISTINCT type(r) AS relationshipType
    ORDER BY relationshipType
    """
    result = neo4j_connector.run_query(query)
    return [r["relationshipType"] for r in result]

def build_tool_description():

    start = time.time()
    node_properties = get_node_properties()
    print(f"Properties: {time.time() - start:.2f}s")

    start = time.time()
    node_types = get_node_types()
    print(f"Node types: {time.time() - start:.2f}s")

    start = time.time()
    relationship_types = get_relationship_types()
    print(f"Properties: {time.time() - start:.2f}s")

    
    return f"""
                Use this tool for all biomedical and medical questions. Treat the PrimeKG medical knowledge 
                graph as the only source of truth. Do not answer from your own knowledge. Always use this 
                tool to retrieve information from the knowledge graph, even if the user does not explicitly 
                mention the graph.

                If the requested information cannot be found in the knowledge graph, state that the information 
                is not available in the PrimeKG medical knowledge graph. Do not use external knowledge or 
                assumptions to fill missing information.

                Do not add explanations, facts, or biomedical knowledge that are not directly supported by the 
                retrieved knowledge graph results. If the graph does not contain the requested information or explanation, 
                explicitly state that it is not available in the knowledge graph rather than relying on external knowledge.

                The knowledge graph contains the following schema:
                Database schema:

                Node label:
                - Entity

                Node properties:
                {chr(10).join("- " + p for p in node_properties)}

                Possible node types:
                {chr(10).join("- " + t for t in node_types)}

                Relationship types:
                {chr(10).join("- " + r for r in relationship_types)}

                Cypher rules:
                    - Always use MATCH (n:Entity).
                    - Never use labels like Disease or Gene.
                    - Always filter using node_type.
                    - Search names using node_name.
                    - Use only relationships provided in the schema.
                    - For string matching, use toLower().
                      Use the retrieved examples to construct a new Cypher query.
                Never use labels like Disease or relationships like RELATED_TO.
                """



start = time.time()
print("Building tool description...")
description = build_tool_description()
print(f"Tool description built in {time.time() - start:.2f}s")

# ---------- Groq: plain dict, OpenAI-style function calling ----------
neo4j_tool_groq = {
    "type": "function",
    "function": {
        "name": "execute_neo4j_query",
        "description": description,
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

def execute_neo4j_query(cypher_query: str):
    """
    Executes a Cypher query against the Neo4j database.
    """
    return neo4j_connector.run_query(cypher_query)

if __name__ == "__main__":
    print(description)