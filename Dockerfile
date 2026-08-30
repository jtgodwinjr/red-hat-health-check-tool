# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production image
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    sshpass openssh-client \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

COPY backend/ ./backend/
COPY --from=frontend-build /app/backend/staticfiles/frontend/ ./backend/staticfiles/frontend/

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV DJANGO_DEBUG=false
ENV DJANGO_SECRET_KEY=changeme-in-production
ENV HEALTHCHECK_DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

VOLUME /data
EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
