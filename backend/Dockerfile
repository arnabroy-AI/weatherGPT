FROM python:3.12-slim-bookworm

WORKDIR /app

# Layer cache: install pinned backend deps before copying sources (D-02).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend sources only. Keys arrive at runtime via compose env_file (D-03);
# no ENV secret lines are set in this image.
COPY main.py ./
COPY api/ ./api/
COPY core/ ./core/
COPY schemas/ ./schemas/
COPY services/ ./services/
COPY tools/ ./tools/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
