from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


class CypherAnswerResponse(BaseModel):
    answer: str
    generated_cypher: str | None = None


class GraphRAGAnswerResponse(BaseModel):
    answer: str
    context_used: str


class RawCypherRequest(BaseModel):
    cypher: str
    params: dict = {}
