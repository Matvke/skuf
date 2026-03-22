from fastapi import FastAPI
from routes import v1_router

app = FastAPI(
    title="Anonymization Engine API",
    version="0.1.0",
)

app.include_router(v1_router)


@app.get("/")
async def home():
    return {"healthy": "true"}
