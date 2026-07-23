"""
FastAPI entrypoint.
"""
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="HealthNexus API")
app.include_router(router)


@app.get("/")
def root():
    return {"message": "HealthNexus API is running"}
