# Se construye desde la RAÍZ del repositorio (necesita fase-2 y fase-4):
#   docker build -f fase-3/Dockerfile -t ames-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY fase-3/requirements.txt fase-3/requirements.txt
RUN pip install -r fase-3/requirements.txt

# Código, datos de ejemplo y versiones v1/v2 (valores por defecto; se pueden montar encima).
COPY fase-2 fase-2
COPY fase-3 fase-3
COPY fase-4 fase-4

# Datos, modelos y registro de Fase 4 se montan como volúmenes en "docker run".
VOLUME ["/app/fase-2/data", "/app/fase-2/models", "/app/fase-4/logs"]

EXPOSE 8000
WORKDIR /app/fase-3
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
