"""
OpenAI-compatible API routes for OpenWebUI.
"""
import json
from fastapi.responses import StreamingResponse
from fastapi import APIRouter
from fastapi import HTTPException
from app.models.schemas import ChatCompletionRequest
from app.core.chat_service import chat, get_models

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


@router.get("/models")
async def list_models():
    return get_models()




@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):

    try:

        stream = chat(
            model=request.model,
            messages=[message.model_dump() for message in request.messages],
        )

        if not request.stream:

            text = ""

            for chunk in stream:
                if chunk.text:
                    text += chunk.text

            return {
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": text,
                        },
                        "finish_reason": "stop",
                    }
                ],
            }

        async def event_stream():

            for chunk in stream:

                if chunk.text:

                    data = {
                        "id": "chatcmpl-1",
                        "object": "chat.completion.chunk",
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "content": chunk.text
                                },
                                "finish_reason": None
                            }
                        ]
                    }

                    yield f"data: {json.dumps(data)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))