import os, json, time
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from backend.config import CHUNKS_JSONL
import re

# 1) Load .env
load_dotenv()  
endpoint   = os.getenv("AZURE_SEARCH_ENDPOINT")
admin_key  = os.getenv("AZURE_SEARCH_ADMIN_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX", "nestle-content")
vector_field = "contentVector"

#Instantiate the client
credential    = AzureKeyCredential(admin_key)
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

'''

#------WILL DELETE ALL DOCS -------- 

results = search_client.search(
    search_text="*",
    select=["id"],
    top=1000,
    include_total_count=True
)

ids = [doc["id"] for doc in results]

print(f"Found {len(ids)} documents; deleting…")

# batch‐delete by key
if ids:
    delete_actions = [{"id": doc_id} for doc_id in ids]
    delete_results = search_client.delete_documents(documents=delete_actions)
    succeeded = sum(1 for r in delete_results if r.succeeded)
    print(f"✅ Deleted {succeeded}/{len(delete_actions)} documents.")
else:
    print(" No documents found to delete.")

'''

#Path to your embeddings.jsonl
EMBEDDINGS_JSONL = os.path.join(os.path.dirname(CHUNKS_JSONL), "embeddings.jsonl")

#Loader
def load_embeddings(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            doc = json.loads(line)
            yield {
                "id":           re.sub(r"[^A-Za-z0-9_\-=]", "_", doc["id"]),
                "url":          doc["metadata"]["url"],
                "domain": doc["metadata"]["domain"],
                "chunk_index":  doc["metadata"]["chunk_index"],
                "text_excerpt": doc["metadata"]["text_excerpt"],
                "timestamp":    doc["metadata"]["timestamp"],
                vector_field:   doc["values"]
            }
#Batcher to reduce calls
def batch_iterator(iterable, size=100):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch

#Upload all embeddings
for batch in batch_iterator(load_embeddings(EMBEDDINGS_JSONL), size=100):
    print(f"Uploading {len(batch)} docs…")
    search_client.upload_documents(documents=batch)
    time.sleep(1)

print("All embeddings uploaded")