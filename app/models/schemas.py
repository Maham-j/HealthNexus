"""
Request/response models.
"""
from pydantic import BaseModel


class RawCypherRequest(BaseModel):
    cypher: str
    params: dict = {}


class RawCypherResponse(BaseModel):
    rows: list[dict]
    count: int
