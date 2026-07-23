from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    QuestionRequest,
    CypherAnswerResponse,
    GraphRAGAnswerResponse,
    RawCypherRequest,
)
from app.chains.cypher_chain import ask_via_cypher
from app.chains.qa_chain import ask_via_graphrag
from app.core.neo4j_connector import neo4j_connector

router = APIRouter()


@router.get("/health")
def health_check():
    neo4j_ok = neo4j_connector.verify_connection()
    return {"status": "ok" if neo4j_ok else "degraded", "neo4j_connected": neo4j_ok}


@router.post("/ask/cypher", response_model=CypherAnswerResponse)
def ask_cypher_endpoint(request: QuestionRequest):
    """
    Path 2: LLM writes its own Cypher query, runs it against Neo4j,
    and turns the result into a plain-English answer.
    """
    try:
        result = ask_via_cypher(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask/graphrag", response_model=GraphRAGAnswerResponse)
def ask_graphrag_endpoint(request: QuestionRequest):
    """
    Path 1: we retrieve graph context ourselves, then the LLM
    reasons over that context to answer.
    """
    try:
        result = ask_via_graphrag(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/raw")
def run_raw_cypher(request: RawCypherRequest):
    """
    For manual testing via Postman — send Cypher directly, skip the LLM
    entirely, get raw table results back.
    """
    try:
        rows = neo4j_connector.run_query(request.cypher, request.params)
        return {"rows": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
