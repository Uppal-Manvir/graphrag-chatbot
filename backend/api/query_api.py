# backend/api/query_api.py

# uvicorn backend.api.query_api:app --reload

"""
This module provides a unified `/query` endpoint that:
  1. Performs a semantic search (vector) against Azure Cognitive Search
  2. Fetches related entities from the Cosmos DB Gremlin graph
  3. Constructs a fused prompt and queries the LLM for an answer

"""

import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from backend.graph_rag.graph_query import query_graph
from openai import OpenAI

# --------------------
# Load environment
# --------------------
load_dotenv()

# Azure Search config
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY"))
)

# OpenAI config
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --------------------
# 2) Initialize FastAPI
# --------------------
app = FastAPI()

# --------------------
# Define request/response models
# --------------------
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    chunk_ids: list
    entity_ids: list

# --------------------
# Unified query endpoint
# --------------------
@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """
    1) Vector-search Azure Cognitive Search
    2) Graph-traverse Cosmos DB Gremlin
    3) Build prompt and query LLM
    """
    # Vector search
    results = search_client.search(
        search_text=req.question,
        top=5
    )
    chunk_ids = [doc["id"] for doc in results]
    snippets = [doc.get("text_excerpt", "") for doc in results]

    # Graph retrieval
    entities = query_graph(chunk_ids, max_hops=1)
    entity_ids = [e["id"] for e in entities]
    entity_summaries = [f"{e['name']} ({e['type']})" for e in entities]

    # Construct fused prompt
    prompt = "Here are the relevant excerpts:\n"
    for snip in snippets:
        prompt += f"- {snip}\n"
    if entity_summaries:
        prompt += "\nHere are related entities:\n"
        for ent in entity_summaries:
            prompt += f"- {ent}\n"
    prompt += f"\nAnswer this question: {req.question}\n"

    # Query the LLM
    response = client.chat.completions.create(
        model="gpt-4o",  # or your chosen deployment
        messages=[{"role":"user","content":prompt}]
    )
    answer = response.choices[0].message.content.strip()

    return QueryResponse(
        answer=answer,
        chunk_ids=chunk_ids,
        entity_ids=entity_ids
    )

