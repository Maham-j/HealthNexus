"""
Path 2 of the project: user asks a question in plain English ->
LLM writes a Cypher query -> query runs on Neo4j -> LLM turns the
table result back into a natural-language answer.

Uses langchain_neo4j's GraphCypherQAChain, which handles the
"generate Cypher, run it, summarize result" loop for us.
"""
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from app.config import settings
from app.core.llm_client import get_llm

_graph = Neo4jGraph(
    url=settings.neo4j_uri,
    username=settings.neo4j_user,
    password=settings.neo4j_password,
    database=settings.neo4j_database,
)


def get_cypher_chain():
    llm = get_llm()
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=_graph,
        verbose=True,
        allow_dangerous_requests=True,  # required flag since this executes generated Cypher
        return_intermediate_steps=True,  # so we can show the actual Cypher used, not just the answer
    )
    return chain


def ask_via_cypher(question: str) -> dict:
    chain = get_cypher_chain()
    result = chain.invoke({"query": question})
    return {
        "answer": result.get("result"),
        "generated_cypher": result.get("intermediate_steps", [{}])[0].get("query"),
    }
