import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_BASE_URL = "http://localhost:11434"

def chat(model: str, messages: list):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }


def get_models():
    response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
    response.raise_for_status()
    return response.json()


    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()

    return response.json()