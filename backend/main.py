from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.query_api import router as query_router   
#main entrance to backend service
app = FastAPI()

#Added cors middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[  # ideally just your frontend URL
        "https://graphragstaticfront.z13.web.core.windows.net",
        "http://localhost:5173"
    ],
    allow_methods=["*"],   # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],   # allow all headers (e.g. Content-Type)
    allow_credentials=True # if you ever need cookies/auth
)

# Mount all your query endpoints at /query
app.include_router(query_router, prefix="/query")

# Health-check endpoint for Docker/ Azure to probe
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

#az acr login --name acrgraphrag
#docker build -t acrgraphrag.azurecr.io/graphrag-backend:latest .
#docker push acrgraphrag.azurecr.io/graphrag-backend:latest
#