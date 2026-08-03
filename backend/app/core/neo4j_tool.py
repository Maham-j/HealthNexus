"""This file's job is only to define the tool and execute the query."""

"""
Neo4j tool for Gemini function calling.
"""

from app.core.neo4j_connector import neo4j_connector



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

def execute_neo4j_query(cypher_query: str):
    """
    Executes a Cypher query against the Neo4j database.
    """
    return neo4j_connector.run_query(cypher_query)