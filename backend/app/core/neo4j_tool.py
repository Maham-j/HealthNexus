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
    print(f"Relationship types: {time.time() - start:.2f}s")

    
    return f"""
            <knowledge_graph>

                <purpose>
                    Execute read-only Cypher queries against the PrimeKG biomedical knowledge graph.
                </purpose>

                <behavior>

                    <priority>
                        Treat the PrimeKG knowledge graph as the primary biomedical source.
                    </priority>

                    <grounding>
                        Always retrieve information from the knowledge graph before answering.
                        Do not rely on internal biomedical knowledge when the graph is applicable.
                    </grounding>

                    <missing_information>
                        If the requested information is unavailable in the knowledge graph,
                        clearly state that it is not available.
                        Do not invent facts or relationships.
                    </missing_information>

                </behavior>

                <schema>

                    <node_label>
                        Entity
                    </node_label>

                    <node_properties>
                        {chr(10).join(f"<property>{p}</property>" for p in node_properties)}
                    </node_properties>

                    <node_types>
                        {chr(10).join(f"<type>{t}</type>" for t in node_types)}
                    </node_types>

                    <relationship_types>
                        {chr(10).join(f"<relationship>{r}</relationship>" for r in relationship_types)}
                    </relationship_types>

                </schema>

                <cypher_rules>

                    <rule>Always use MATCH (n:Entity).</rule>
                    <rule>Never use labels like Disease or Gene.</rule>
                    <rule>Filter entity types using node_type.</rule>
                    <rule>Search names using node_name.</rule>
                    <rule>Use only relationship types listed in the schema.</rule>
                    <rule>Use toLower() for string matching.</rule>
                    <rule>Generate only read-only Cypher queries.</rule>
                    <rule>Prefer adding LIMIT 100 in Cypher queries that could match many rows, especially broad disease/gene relationship lookups.</rule>
                    <rule>When filtering by keyword in a name (e.g. CONTAINS 'familial', 'hereditary', 'syndrome', 'susceptibility'), treat this as a weak text-matching heuristic, not a confirmed classification — state this limitation explicitly when presenting such results.</rule>
                </cypher_rules>

            </knowledge_graph>
            """


start = time.time()
print("Building tool description...")
description = build_tool_description()
print(f"Tool description built in {time.time() - start:.2f}s")


def execute_neo4j_query(cypher_query: str, max_results: int = 100):
    """
    Executes a Cypher query against the Neo4j database.
    Truncates results so oversized result sets can't blow the LLM's token budget.
    """
    results = neo4j_connector.run_query(cypher_query)

    if len(results) > max_results:
        truncated = results[:max_results]
        return {
            "results": truncated,
            "note": f"Showing {max_results} of {len(results)} total results. "
                    f"The query matched more rows than shown here.",
        }

    return results

if __name__ == "__main__":
    print(description)