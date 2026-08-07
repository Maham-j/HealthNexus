from app.core.rag_tool import get_rag_tool, FAISS_TOOL_DESCRIPTION
from app.core.neo4j_tool import execute_neo4j_query, description as NEO4J_TOOL_DESCRIPTION
from langchain.tools import tool


@tool(description=FAISS_TOOL_DESCRIPTION)
def fetch_similar_queries(query: str):
    return get_rag_tool().fetch_similar_queries(query)


@tool(description=NEO4J_TOOL_DESCRIPTION)
def run_neo4j_query(cypher_query: str):
    return execute_neo4j_query(cypher_query)


tools = [
    fetch_similar_queries,
    run_neo4j_query,
]