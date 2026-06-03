FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DASHBOARD_UPLOAD_DIR=/app/data/uploads
ENV DASHBOARD_IMPORT_SERVICE_SRC=/app/import-service/src

WORKDIR /app

COPY backend-api/pyproject.toml backend-api/pyproject.toml
COPY backend-api/src backend-api/src
COPY import-service/pyproject.toml import-service/pyproject.toml
COPY import-service/src import-service/src

RUN python -m pip install --no-cache-dir --upgrade pip \
  && python -m pip install --no-cache-dir -e backend-api -e import-service

RUN mkdir -p /app/data/uploads

EXPOSE 8000

CMD ["uvicorn", "dashboard_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
