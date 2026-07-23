"""
Path 1 of the project: GraphRAG.
Instead of the LLM writing Cypher itself, WE retrieve relevant graph
context (nodes/relationships) first using our own retrieval logic,
then hand that context to the LLM to reason over and answer.

This file is a starting stub — the actual retrieval strategy
(vector index vs keyword match vs fixed traversal patterns) is the
next thing to design with the team.
"""
from app.core.neo4j_connector import neo4j_connector
from app.core.llm_client import get_llm
from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are a medical knowledge assistant. Use ONLY the graph context
below to answer the question. If the context doesn't contain the answer,
say so — do not make up information.

Graph context:
{context}

Question: {question}

Answer:"""
)


def retrieve_context(question: str, limit: int = 25) -> str:
    """
    Placeholder retrieval: naive name-match lookup against Entity nodes.
    Replace with a proper retrieval strategy (embeddings / full-text index /
    entity linking) once that part of the design is decided.
    """
    cypher = """
    MATCH (n:Entity)
    WHERE toLower(n.node_name) CONTAINS toLower($keyword)
    OPTIONAL MATCH (n)-[r]-(m:Entity)
    RETURN n.node_name AS entity, n.node_type AS type,
           type(r) AS relation, m.node_name AS related_entity
    LIMIT $limit
    """
    # Very naive keyword extraction for now — first noun-ish word in the question.
    keyword = question.split()[-1]
    rows = neo4j_connector.run_query(cypher, {"keyword": keyword, "limit": limit})
    if not rows:
        return "No matching graph context found."
    return "\n".join(str(row) for row in rows)


def ask_via_graphrag(question: str) -> dict:
    context = retrieve_context(question)
    llm = get_llm()
    chain = RAG_PROMPT | llm
    response = chain.invoke({"context": context, "question": question})
    return {
        "answer": response.content,
        "context_used": context,
    }
