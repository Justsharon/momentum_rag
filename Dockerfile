FROM python:3.11-slim

WORKDIR /app

# Install deps first so this layer is cached across code changes.
# Uses requirements-api.txt (not requirements.txt) -- deliberately excludes
# eval-only packages that aren't imported by api.py.
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Only copy what the API actually imports -- api.py depends on retrieval.py
# and llm.py, nothing else. Evaluation scripts (retrieval_eval.py, etc.) are
# run manually on your host, not shipped in this image.
COPY retrieval.py llm.py api.py ./

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]