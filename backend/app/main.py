from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Keitaro Wrapper")
app.include_router(router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

