"""
Request/response models.
"""
from pydantic import BaseModel
from typing import List

class RawCypherRequest(BaseModel):
    cypher: str
    params: dict = {}


class RawCypherResponse(BaseModel):
    rows: list[dict]
    count: int


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False