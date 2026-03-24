FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Installa dipendenze (backend include già quelle di ai-service)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia entrambe le cartelle
COPY backend/ ./backend/
COPY ai-service/ ./ai-service/

WORKDIR /app/backend

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
