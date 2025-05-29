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
  docker build -t acrgraphrag.azurecr.io/graphrag-backend:latest .
  docker push acrgraphrag.azurecr.io/graphrag-backend:latest
(Common error make sure you are logged into Azure Container Registry)
Update Azure App Service (or Container App) to use the new image.
Verify health probe is running at /healthz (should return 200)
---
## 🧰 Data Ingestion Pipeline  
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
GraphRAG Module Instructions
Ingest site content into Azure Cognitive Search index (see backend/ingest_acs.py).

Populate Cosmos DB Gremlin graph with nodes and edges (via backend/graph_rag/graph_ingest.py).

Query the graph and search together: /query endpoint performs both vector search and graph traversal.

To extend: add new nodes/relationships using the Gremlin API, then re-run ingestion scripts.

---

Known Limitations

Scaling: Dev tiers (Free/Basic) are low-throughput; upgrade for high traffic.

Costs: Azure Search and OpenAI usage can accrue charges—monitor your subscription and consider local OSS for dev.



