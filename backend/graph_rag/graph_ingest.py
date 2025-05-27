
import os
import json
import re
import time
from dotenv import load_dotenv
from gremlin_python.driver.client import Client
from gremlin_python.driver.serializer import GraphSONSerializersV2d0
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

# --------------------
# 1) Load environment
# --------------------
load_dotenv()
GREMLIN_ENDPOINT        = os.getenv("COSMOS_ENDPOINT")       
GREMLIN_KEY             = os.getenv("COSMOS_KEY")            
COSMOS_DB               = os.getenv("COSMOS_DATABASE")      
COSMOS_GRAPH            = os.getenv("COSMOS_GRAPH")        
EMBEDDINGS_JSONL        = os.getenv("EMBEDDINGS_JSONL_PATH")  
TEXT_ANALYTICS_ENDPOINT = os.getenv("TEXT_ANALYTICS_ENDPOINT")
TEXT_ANALYTICS_KEY      = os.getenv("TEXT_ANALYTICS_KEY")     

# --------------------
# 2) Sanity check
# --------------------
missing = [name for name, val in [
    ("COSMOS_ENDPOINT", GREMLIN_ENDPOINT),
    ("COSMOS_KEY",      GREMLIN_KEY),
    ("COSMOS_DATABASE", COSMOS_DB),
    ("COSMOS_GRAPH",    COSMOS_GRAPH),
    ("EMBEDDINGS_JSONL_PATH", EMBEDDINGS_JSONL),
    ("TEXT_ANALYTICS_ENDPOINT", TEXT_ANALYTICS_ENDPOINT),
    ("TEXT_ANALYTICS_KEY", TEXT_ANALYTICS_KEY)
] if not val]
if missing:
    raise RuntimeError(
        f"Missing env-vars: {', '.join(missing)}."
        " Make sure your .env includes these keys."
    )
print("Env vars loaded successfully.")

# --------------------
# 3) Instantiate Gremlin client
# --------------------
# 
gremlin_client = Client(
    GREMLIN_ENDPOINT, 'g',
    username=f"/dbs/{COSMOS_DB}/colls/{COSMOS_GRAPH}",
    password=GREMLIN_KEY,
    message_serializer=GraphSONSerializersV2d0()
)

# --------------------
# 4) Instantiate Text Analytics client
# --------------------
text_credential = AzureKeyCredential(TEXT_ANALYTICS_KEY)
taa_client = TextAnalyticsClient(
    endpoint=TEXT_ANALYTICS_ENDPOINT,
    credential=text_credential
)

# --------------------
# 5) Upsert data
# --------------------

def upsert_chunk(chunk):
    future = gremlin_client.submitAsync(
        """
        g.V().has('Chunk','id', chunkId).fold()
         .coalesce(
           unfold(),
           addV('Chunk')
             .property('id', chunkId)
             .property('partitionKey', chunkId)
         )
         .property('url', url)
         .property('text_excerpt', excerpt)
         .property('timestamp', ts)
        """,
        {
            "chunkId": chunk["id"],
            "url":     chunk["url"],
            "domain": chunk["domain"],
            "excerpt": chunk["text_excerpt"],
            "ts":      chunk["timestamp"]
        }
    )
    future.result()


def upsert_entity(entity):
    try:
        future = gremlin_client.submitAsync(
            """
            g.V().has('Entity','id', entId).fold()
            .coalesce(
            unfold(),
            addV('Entity')
                .property('id', entId)
                .property('partitionKey', entId)
            )
            .property('name', name)
            .property('type', etype)
            """,
            {
                "entId": entity["id"],
                "name":  entity["name"],
                "etype": entity["type"]
            }
        )
    except Exception as e:
        if "409" in str(e):
            # already exists, so ignore
            return
        raise
    future.result()


def link_contains(chunk_id, ent_id, confidence):
    """
    Upsert a 'contains' edge between a Chunk and an Entity.
    Uses matching placeholders (chunkId, entId) in the Gremlin query and binding dict.
    """
    gremlin_query = """
    g.V().has('Chunk','id', chunkId)
      .coalesce(
        outE('contains').where(inV().has('Entity','id', entId)),
        addE('contains')
          .from(g.V().has('Chunk','id', chunkId))
          .to(g.V().has('Entity','id', entId))
          .property('confidence', confidence)
      )
    """
    gremlin_client.submitAsync(
        gremlin_query,
        {
            "chunkId":   chunk_id,
            "entId":     ent_id,
            "confidence": confidence
        }
    ).result()

# --------------------
# 6) Entity extraction via Azure Text Analytics
# --------------------

def extract_entities(text):
    try:
        response = taa_client.recognize_entities([text])[0]
        entities = []
        for ent in response.entities:
            eid = re.sub(r"[^A-Za-z0-9]", "_", ent.text.lower())
            entity = {"id": eid, "name": ent.text, "type": ent.category}
            confidence = ent.confidence_score
            entities.append((entity, confidence))
        return entities
    except Exception as e:
        print("Entity extraction failed:", e)
        return []

# --------------------
# 7) Loader for embeddings
# --------------------

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
                "timestamp":    doc["metadata"]["timestamp"]
            }


def batch_iterator(iterable, size=100):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch

# --------------------
# 8) Full ingestion loop
# --------------------

def ingest_graph():
    for batch in batch_iterator(load_embeddings(EMBEDDINGS_JSONL), size=50):
        for doc in batch:
            upsert_chunk(doc)
            ents = extract_entities(doc["text_excerpt"])
            for entity, conf in ents:
                upsert_entity(entity)
                link_contains(doc["id"], entity["id"], conf)
        time.sleep(1)
    print("Graph ingestion complete!")



if __name__ == "__main__":
    print("Starting GraphRAG ingestion...")
    ingest_graph()
    gremlin_client.close()

