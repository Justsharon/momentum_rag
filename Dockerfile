FROM python:3.11-slim

WORKDIR /app

# Install deps first so this layer is cached across code changes.
# Uses requirements-api.txt (not requirements.txt) -- deliberately excludes
# eval-only packages that aren't imported by api.py.
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Copies every module api.py actually imports, directly or transitively:
# api.py -> retrieval, llm, indexing, documents, model
# retrieval.py -> embeddings
# indexing.py -> embeddings, chunking, model
# documents.py -> model
# Evaluation scripts (retrieval_eval.py, etc.) are run manually on your
# host, not shipped in this image.
COPY api.py retrieval.py llm.py indexing.py documents.py model.py \
     embeddings.py chunking.py ./

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]