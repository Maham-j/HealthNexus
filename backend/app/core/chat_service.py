from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def chat(model: str, messages: list):

    prompt = "\n".join(
        [message["content"] for message in messages]
    )

    return client.models.generate_content_stream(
        model=model,
        contents=prompt,
    )

def get_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "gemini-3.6-flash",
                "object": "model",
                "owned_by": "google"
            }
        ]
    }