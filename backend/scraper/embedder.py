from dotenv import load_dotenv
import os, json, time
from backend.config import CHUNKS_JSONL  # path to data/chunks.jsonl
from openai import OpenAI


# Store embedding
OUTPUT_PATH = os.path.join(os.path.dirname(CHUNKS_JSONL), 'embeddings.jsonl')

# setup openai api and limits
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL        = "text-embedding-ada-002"
BATCH_SIZE   = 100   # send ~100 chunks per API call

def load_chunks(path):
    """Yield each chunk record from chunks.jsonl in our case"""
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)

def batch_iterator(iterable, size):
    """Group items into lists of length size 
        ex: chunks into list of lengh 100
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch

def main():
    #Setup output
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as out_f:
        #Iterate over each batch of chunk records
        for batch in batch_iterator(load_chunks(CHUNKS_JSONL), BATCH_SIZE):
            texts = [rec['text'] for rec in batch]
            #print(texts)
            # call embedding
            # for t in texts:
            #     print(f"- {repr(t)} (type: {type(t)}, len: {len(t)})")
            response = client.embeddings.create(
                model= MODEL,
                input=texts 
            )
            embeddings = response.data  # list of {index, embedding}
            
            #print(embeddings)

            # Write each embedding + metadata as one JSON line into embeddings.jsonl
            for emb_item, rec in zip(embeddings, batch):
                out_record = {
                    "id": f"{rec['url']}#chunk{rec['chunk_index']}",
                    "values": emb_item.embedding,
                    "metadata": {
                        "url":         rec['url'],
                        "chunk_index": rec['chunk_index'],
                        "text_excerpt": rec['text'][:100],
                        "timestamp":    rec['timestamp']
                    }
                }
                out_f.write(json.dumps(out_record, ensure_ascii=False) + "\n")

            
            time.sleep(1)

    print(f"Embeddings written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()