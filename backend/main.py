from fastapi import FastAPI
from api.query_api import router as query_router   # your existing FastAPI router

app = FastAPI()

# Mount all your query endpoints at /query
app.include_router(query_router, prefix="/query")

# Health-check endpoint for Docker/ Azure to probe
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}