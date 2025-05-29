import json
from backend.config import PAGES_JSONL, CHUNKS_JSONL
from backend.scraper.utils import infer_domain_from_url

'''
Breaks down scraped pages into chunks of 3000 chars and categorises them into groups for more optomized searches
'''

MAX_CHARS = 3000

#Split into chunks of MAX_CHAR
def chunk_text(text): 
    paras = text.split('. ')
    chunks, buffer = [], ""
    for p in paras:
        if len(buffer) + len(p) + 2 < MAX_CHARS:
            buffer += p + '. '
        else:
            chunks.append(buffer.strip())
            buffer = p + '. '
    if buffer:
        chunks.append(buffer.strip())
    return chunks

#Read pages from pages jsonl and writes each chunk with its index and domain into chunks json
with open(PAGES_JSONL, 'r', encoding='utf-8') as infile, open(CHUNKS_JSONL, 'w', encoding='utf-8') as out:
    for line in infile:
        rec = json.loads(line)
        print("added chunk")
        for i, chunk in enumerate(chunk_text(rec['text'])):
            if len(chunk) > 0:
                domain = infer_domain_from_url(rec['url'])
                out.write(json.dumps({
                    "url": rec['url'],
                    "timestamp": rec['timestamp'],
                    "domain": domain,
                    "chunk_index": i,
                    "text": chunk
                }) + "\n")
