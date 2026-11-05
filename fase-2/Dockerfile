FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Codigo y datos de ejemplo. No se entrena durante el build ni se define ENTRYPOINT:
# el comando (train.py o predict.py) se indica en cada "docker run".
COPY . .
