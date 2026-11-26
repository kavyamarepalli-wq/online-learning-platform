# Single-container deployment: the API also serves the built website.
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN API_URL= npm run build

FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY database/ database/
COPY --from=frontend /build/dist frontend/dist
RUN useradd --create-home appuser && mkdir -p backend/uploads backend/instance \
    && chown -R appuser backend/uploads backend/instance
USER appuser
ENV APP_ENV=production PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "gunicorn --chdir backend --workers 2 --threads 4 --timeout 300 --bind 0.0.0.0:$PORT wsgi:app"]
