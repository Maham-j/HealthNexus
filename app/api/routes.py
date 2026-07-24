"""
API routes.
"""
from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import RawCypherRequest, RawCypherResponse
from app.core.neo4j_connector import neo4j_connector
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/health")
def health_check():
    neo4j_ok = neo4j_connector.verify_connection()
    return {"status": "ok" if neo4j_ok else "degraded", "neo4j_connected": neo4j_ok}


@router.post("/query/raw", response_model=RawCypherResponse)
def run_raw_cypher(request: RawCypherRequest, current_user: str = Depends(get_current_user)):
    """
    Manual testing endpoint — now requires a valid JWT (Bearer token)
    in the Authorization header. Get one via POST /auth/login first.
    """
    try:
        rows = neo4j_connector.run_query(request.cypher, request.params)
        return {"rows": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TODO: /ask/cypher
# TODO: /ask/graphrag
