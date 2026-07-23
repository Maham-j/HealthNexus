from fastapi import FastAPI
from app.api.routes import router
from app.config import settings

app = FastAPI(
    title="HealthNexus API",
    description="Medical Knowledge Graph & Clinical Reasoning System — GraphRAG over Neo4j",
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "HealthNexus API is running",
        "env": settings.app_env,
    }
