"""
API routes. TODO: implement endpoints.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}

# TODO: /ask/cypher
# TODO: /ask/graphrag
# TODO: /query/raw
