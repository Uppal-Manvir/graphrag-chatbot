# NestléSiteBot Chatbot

**Live Demo:** [Backend API](https://rg-chatbot-eafyfwgkg4e5djef.canadaeast-01.azurewebsites.net)  
**Frontend (Static Site):** https://graphragstaticfront.z13.web.core.windows.net

---

##  Project Overview
This repository contains a full-stack AI-based chatbot for [madewithnestle.ca](https://www.madewithnestle.ca), featuring:

- **GraphRAG Module**: Combines vector search (Azure Cognitive Search) with graph-based traversal (Cosmos DB Gremlin) to retrieve contextually rich snippets and entity relationships.
- **FastAPI Backend**: Exposes a `/query` endpoint for processing user questions and returning answers.
- **Vite + React Frontend**: A static site that calls the backend API and displays responses.
- **Azure Deployment**: Backend on Azure App Service, frontend on Azure Static Website.
- 

---

##  Prerequisites
- **Node.js & npm** (v16+)
- **Python** (3.10+) with `pip`
- **Azure CLI** (for optional tooling)
- Azure resources:
  - **Azure Cognitive Search** 
  - **Azure Cosmos DB (Gremlin API)**
  - **Azure OpenAI** (or OpenAI API key)

---

##  Environment Variables
Create a `.env` in the **backend/** folder:

```env
AZURE_SEARCH_ENDPOINT=<your-search-endpoint>
AZURE_SEARCH_INDEX=<index-name>
AZURE_SEARCH_ADMIN_KEY=<admin-key>
AZURE_COSMOS_ENDPOINT=<cosmos-endpoint>
AZURE_COSMOS_KEY=<cosmos-key>
COSMOS_DATABASE=<cosmos-db>
COSMOS_GRAPH=<cosmos-graph>
OPENAI_API_KEY=<openai-key>
EMBEDDINGS_JSONL_PATH=backend/data/embeddings.jsonl


##  Environment Variables
Create a `.env`and `.env.production` in the **frontend/** folder:

.env
VITE_API_URL= <vite-api-url>

.env.production (production url)
VITE_API_URL= <vite-production-api-url>
```
---

## Local Development

Backend:
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

Frontend
cd frontend
npm install
npm run dev

---

## Production Development

cd frontend
npm run build

This will create a /dist folder that you need to uplaod into Azure static website under the $web container. (Could also do it via azure ALI)
Build and push docker image into Azure Container Registry
```
  docker build -t acrgraphrag.azurecr.io/graphrag-backend:latest .
  docker push acrgraphrag.azurecr.io/graphrag-backend:latest

#(Common error make sure you are logged into Azure Container Registry)
#Update Azure App Service (or Container App) to use the new image.
#Verify health probe is running at /healthz (should return 200)
```
---
## 🔄 System Architecture & Data Flow

1. **Data Ingestion**  
   - **Scraper** (`backend/ingest_acs.py`): BFS crawl (via Selenium) of madewithnestle.ca → raw docs  
   - **Chunker** (`backend/scraper/chunker.py`): splits each page into ~3,000-char chunks  
   - **Embedder** (`backend/scraper/embedder.py`): calls OpenAI embeddings → writes to Azure Cognitive Search  
   - **Graph Ingest** (`backend/graph_rag/graph_ingest.py`): loads entities & edges into Cosmos DB Gremlin  

2. **Runtime Query**  
   1. Frontend POSTS user question to `POST /query`  
   2. FastAPI backend does **vector search** (Azure Search) → returns top-K chunk IDs + snippets  
   3. FastAPI backend does **graph traversal** (Cosmos DB Gremlin) on those chunk IDs → related entities  
   4. **Fused prompt** builder merges snippets + entity summaries + system persona  
   5. LLM call (OpenAI / Azure OpenAI) → an answer  
   6. Backend returns `QueryResponse` JSON → frontend renders  
---
## 🧰 Data Ingestion Pipeline Breakdown
Before the chatbot can answer, run these steps:
After activating python venv 

1. **Scraper**  - Goes from sitemap and find all urls, scrpaes each url and also finds any nested urls and adds to scrape queue. Note view limitation
   ```bash
   cd backend
   python -m backend.scraper.scraper
   ```
2. **Chunker** - Breaks down scraped pages into chunks of 3000 chars and categorises them into groups for more optomized searches
   ```
   cd backend
   python -m backend.scraper.chunker
   ```
3. **Embedder** - Generates embeddings for chunked data to be uploaded 
   ```
   cd backend
   python -m backend.scraper.embedder
   ```
3. ++Upload embedding to Azure search
   ```
   python -m backend.vector_store.ingest_acs
   ```
---
## GraphRAG Module Instructions
Ingest site content into Azure Cognitive Search index (see backend/ingest_acs.py).

Populate Cosmos DB Gremlin graph with nodes and edges (via backend/graph_rag/graph_ingest.py).

Query the graph and search together: /query endpoint performs both vector search and graph traversal.

To extend: add new nodes/relationships using the Gremlin API, then re-run ingestion scripts.

---

## Known Limitations / Future Improvements

**Scaling:**
Dev tiers (Free/Basic) are low-throughput; upgrade for high traffic.

**Costs:**
Azure Search and OpenAI usage can accrue charges—monitor your subscription and consider local OSS for dev. Gets very expensive fast

**Scraping:**
Due to scraping off of production URL had to work around cloudflare bot protection blocking, could not use default requests to get sites had to go through selenium and headed. This caused issues that would not happen with a local version including scraping being slow as it goes through the site in a BFS search finding all URL's. If we had a case where we had access to local version of made with nestle scraping could be a lot more efficent data for graphs and embedding would be complete without missing sections from taking so long all in all calling for way better responses from the chatbot. 

**Incrimental re-ingestion:**
Right now we re-scrape and re-embed on every run; a change-feed or webhook-driven pipeline would allow only new/updated pages to be processed, saving cost and time.

 **Runtime Graph Editing**  
Allow administrators to add nodes/edges via a simple API (e.g. `POST /graph/node`, `POST /graph/edge`) so the knowledge graph can be enriched without re-ingesting everything.





