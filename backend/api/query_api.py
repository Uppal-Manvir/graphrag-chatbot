# backend/api/query_api.py

# uvicorn backend.api.query_api:app --reload

"""
This module provides a unified `/query` endpoint that:
  1. Performs a semantic search (vector) against Azure Cognitive Search
  2. Fetches related entities from the Cosmos DB Gremlin graph
  3. Constructs a fused prompt and queries the LLM for an answer

"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from backend.graph_rag.graph_query import query_graph
from openai import OpenAI

DOMAIN_PROMPT = """
You are a Nestlé chatbot. Classify user questions into exactly one of these domains:
- product (questions about product names, ingredients, nutrition)
- recipe (questions about cooking, ingredients lists, steps)
- policy (questions about privacy policy, terms, cookies)
- off-topic (anything else)

Respond with a single word: product, recipe, policy, or off-topic.
"""

SYSTEM_PROMPT = """
You are NestléSiteBot, the official virtual assistant for madewithnestle.ca.
• You help users find and understand news, articles, recipes, products, and other content on the site.
• Tone: friendly, clear, brand-consistent, and helpful.
• Always use official Nestlé branding and product names including in recipes and include urls for recipes to the full recipe site from the context you are given.
• Cite the source when quoting any excerpt.
• If the answer isn’t in the provided context, direct users back to the appropriate section of madewithnestle.ca.
Dont mention the context or excerpts i provide you the user shouldnt see im providing you context. Only be positive and helpful never negative about the company
"""

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


def detect_domain_llm(question: str) -> str:
    resp = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role":"system", "content": DOMAIN_PROMPT},
        {"role":"user", "content": question}
      ],
      temperature=0.0
    )
    domain = resp.choices[0].message.content.strip().lower()
    # sanitize
    print(domain)
    return domain if domain in {"product","recipe","policy"} else "off-topic"

# --------------------
# 2) Initialize FastAPI
# --------------------
router = APIRouter()

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
@router.post("", response_model=QueryResponse)
def query(req: QueryRequest):
    """
    1) Vector-search Azure Cognitive Search
    2) Graph-traverse Cosmos DB Gremlin
    3) Build prompt and query LLM
    """
    #print("HIT QUERY ENDPOINT")
    # Vector search
    domain = detect_domain_llm(req.question)
    if not domain:
        # off-topic
        raise HTTPException(
            status_code=400,
            detail="Sorry—I only answer questions about Nestlé products, recipes, or policies."
        )
    results = search_client.search(
        search_text=req.question,
        top=5
    )
    chunk_ids = [doc["id"] for doc in results]
    snippets = [doc.get("text_excerpt", "") for doc in results]
    if not chunk_ids: #empty chunk ids crashes gremlin query fix later
        return []
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
        messages=[{
            "role": "system", "content": SYSTEM_PROMPT,
            "role":"user","content":prompt
            }]
    )
    answer = response.choices[0].message.content.strip()

    return QueryResponse(
        answer=answer,
        chunk_ids=chunk_ids,
        entity_ids=entity_ids
    )

