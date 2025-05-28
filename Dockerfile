# Dockerfile (place at the very root of your repo)
FROM python:3.10-slim

# base directory
WORKDIR /usr/src/app

# 2) Copy entire project into root
COPY . .

# 3) Install your Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 80

# 4) Run Uvicorn on 0.0.0.0 and the PORT env var (default to 80)
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-80}"]