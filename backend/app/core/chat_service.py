from app.core.langchain_agent import ask_agent, llm
from langchain_core.messages import HumanMessage, AIMessage
#from app.core.langchain_agent import ask_agent_llm_summary as ask_agent, llm as llm
import time


METADATA_PATTERNS = [
    "### task:",
    "generate a concise",
    "generate 1-3 broad tags",
    "suggest 3-5 relevant follow-up questions",
]


def is_metadata_request(messages: list) -> bool:
    if not messages:
        return False
    content = messages[-1].get("content", "").lower()
    return any(p in content for p in METADATA_PATTERNS)


def chat(model: str, messages: list):
    print("MODEL RECEIVED:", model)

    if not (model.startswith("llama") or model.startswith("openai/gpt-oss")):
        return {"text": "Unsupported model.", "tool_call": False}

    start = time.time()

    if is_metadata_request(messages):
        print("METADATA REQUEST - SKIPPING AGENT")
        try:
            response = llm.invoke(messages[-1]["content"])
            text = response.content
        except Exception as e:
            print("METADATA CALL FAILED:", e)
            text = ""
        return {"text": text, "tool_call": False}

    try:
        answer = ask_agent(messages[-1]["content"], build_chat_history(messages))
    except Exception as e:
        print("LANGCHAIN ERROR:", e)
        return {"text": "I had trouble processing that — could you try again?", "tool_call": False}

    print(f"Total time: {time.time() - start:.2f}s")
    return {"text": answer, "tool_call": True}


def build_chat_history(messages: list):
    history = []
    for m in messages[:-1]:
        if m["role"] == "user":
            history.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            history.append(AIMessage(content=m["content"]))
    return history


def get_models():
    print("GETTING MODELS")
    return {
        "object": "list",
        "data": [
            {"id": "llama-3.3-70b-versatile", "object": "model", "owned_by": "groq"},
            {"id": "openai/gpt-oss-120b", "object": "model", "owned_by": "groq"},
        ]
    }