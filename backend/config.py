import os

BACKEND_ROOT = os.path.dirname(__file__)
DATA_DIR     = os.path.join(BACKEND_ROOT, 'data')
PAGES_JSONL  = os.path.join(DATA_DIR, 'pages.jsonl')
CHUNKS_JSONL = os.path.join(DATA_DIR, 'chunks.jsonl')

