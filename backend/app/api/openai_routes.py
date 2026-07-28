"""
OpenAI-compatible API routes for OpenWebUI.
"""

from fastapi import APIRouter
from app.core.ollama_client import chat
from fastapi import HTTPException
from app.models.schemas import ChatCompletionRequest
from app.core.ollama_client import get_models

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


@router.get("/models")
async def list_models():
    ollama_models = get_models()

    return {
        "object": "list",
        "data": [
            {
                "id": model["name"],
                "object": "model",
                "owned_by": "ollama",
            }
            for model in ollama_models["models"]
        ],
    }


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):

    try:
        response = chat(
            model=request.model,
            messages=[message.model_dump() for message in request.messages]
        )

        return {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response["message"]["content"]
                    },
                    "finish_reason": "stop"
                }
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))