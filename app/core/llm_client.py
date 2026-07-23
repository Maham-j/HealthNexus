"""
Picks and configures the LLM based on LLM_PROVIDER in .env.
Keeping this separate means swapping providers (Gemini <-> OpenAI <-> Groq)
never touches the chain/endpoint logic.
"""
from app.config import settings


def get_llm():
    provider = settings.llm_provider.lower()

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.1-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
