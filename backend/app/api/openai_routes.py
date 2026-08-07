"""
OpenAI-compatible API routes for OpenWebUI.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatCompletionRequest
from app.core.chat_service import chat, get_models
import json


router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


@router.get("/models")
async def list_models():
    return get_models()



@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    print("CHAT ENDPOINT HIT")
    try:
        response = chat(
            model=request.model,
            messages=[message.model_dump() for message in request.messages],
        )
        text = response["text"]

        if not request.stream:
            return {
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
            }

        def event_stream():
            chunk_size = 40
            for i in range(0, len(text), chunk_size):
                piece = text[i:i + chunk_size]
                data = {
                    "id": "chatcmpl-1",
                    "object": "chat.completion.chunk",
                    "choices": [
                        {"index": 0, "delta": {"content": piece}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        print("ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hello")
async def hello():
    print("HELLO ROUTE HIT")
    return {
        "message": "This is MY backend"
    }