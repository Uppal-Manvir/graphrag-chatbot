# 1) Base image with Python 3.10
FROM python:3.10-slim

# 2) Working directory inside the container
WORKDIR /app

# 3) Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy your code
COPY ./api ./api
COPY main.py .

# 5) Expose port 80
EXPOSE 80

# 6) Container-level health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD curl -f http://localhost/healthz || exit 1

# 7) Start FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
