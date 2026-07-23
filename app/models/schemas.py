"""
Request/response models. TODO: define as needed.
"""
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
