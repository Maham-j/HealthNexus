"""
API routes.
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import RawCypherRequest, RawCypherResponse
from app.core.neo4j_connector import neo4j_connector

router = APIRouter()


@router.get("/health")
def health_check():
    neo4j_ok = neo4j_connector.verify_connection()
    return {"status": "ok" if neo4j_ok else "degraded", "neo4j_connected": neo4j_ok}


@router.post("/query/raw", response_model=RawCypherResponse)
def run_raw_cypher(request: RawCypherRequest):
    """
    Manual testing endpoint — send Cypher directly via Postman,
    no LLM involved, get raw table results back as JSON.
    """
    try:
        rows = neo4j_connector.run_query(request.cypher, request.params)
        return {"rows": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TODO: /ask/cypher
# TODO: /ask/graphrag
