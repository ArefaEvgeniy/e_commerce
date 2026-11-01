FROM python:3.12-slim-bookworm

ARG TARGETARCH

# --------------------------------------------------
# System variables
# --------------------------------------------------

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PGDATA=/var/lib/postgresql/data \
    DEBUG=False

WORKDIR /app

# --------------------------------------------------
# Build arguments: values from GitHub Secrets
# --------------------------------------------------

ARG SECRET_KEY
ARG ALLOWED_HOSTS

ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD

ARG DEFAULT_EMAIL_FROM
ARG APP_MAIL_PWD
ARG EMAIL_HOST_USER
ARG EMAIL_HOST_PASSWORD

ARG STRIPE_SECRET_KEY
ARG STRIPE_PUBLISHABLE_KEY

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_KEY
ARG AWS_S3_PUBLIC_ENDPOINT_URL
ARG AWS_STORAGE_BUCKET_NAME

ARG BUILD_VERSION=local

# --------------------------------------------------
# Runtime environment
# --------------------------------------------------

ENV SECRET_KEY="${SECRET_KEY}" \
    ALLOWED_HOSTS="${ALLOWED_HOSTS}" \
    DB_NAME="${DB_NAME}" \
    DB_USER="${DB_USER}" \
    DB_PASSWORD="${DB_PASSWORD}" \
    DB_HOST="127.0.0.1" \
    DB_PORT="5432" \
    DEFAULT_EMAIL_FROM="${DEFAULT_EMAIL_FROM}" \
    APP_MAIL_PWD="${APP_MAIL_PWD}" \
    EMAIL_HOST_USER="${EMAIL_HOST_USER}" \
    EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD}" \
    STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY}" \
    STRIPE_PUBLISHABLE_KEY="${STRIPE_PUBLISHABLE_KEY}" \
    CELERY_BROKER_URL="redis://127.0.0.1:6379/0" \
    CELERY_RESULT_BACKEND="redis://127.0.0.1:6379/1" \
    AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
    AWS_SECRET_KEY="${AWS_SECRET_KEY}" \
    AWS_S3_ENDPOINT_URL="http://127.0.0.1:9000" \
    AWS_S3_PUBLIC_ENDPOINT_URL="${AWS_S3_PUBLIC_ENDPOINT_URL}" \
    AWS_STORAGE_BUCKET_NAME="${AWS_STORAGE_BUCKET_NAME}" \
    BUILD_VERSION="${BUILD_VERSION}" \
    MINIO_ROOT_USER="${AWS_ACCESS_KEY_ID}" \
    MINIO_ROOT_PASSWORD="${AWS_SECRET_KEY}"

# --------------------------------------------------
# Install system packages
# --------------------------------------------------

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        gcc \
        build-essential \
        libpq-dev \
        openssl \
        supervisor \
        nginx \
        redis-server \
        && install -d /usr/share/postgresql-common/pgdg \
        && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
           | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg \
        && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
           > /etc/apt/sources.list.d/pgdg.list \
        && apt-get update \
        && apt-get install -y --no-install-recommends postgresql-16 \
        && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Install MinIO
# --------------------------------------------------

RUN curl -fsSL \
    "https://dl.min.io/server/minio/release/linux-${TARGETARCH}/minio" \
    -o /usr/local/bin/minio \
    && chmod +x /usr/local/bin/minio

# --------------------------------------------------
# Install Python dependencies
# --------------------------------------------------

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------
# Copy project
# --------------------------------------------------

COPY . .

# --------------------------------------------------
# Copy service configurations
# --------------------------------------------------

COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/start-app.sh /start-app.sh
COPY docker/supervisord.conf /etc/supervisor/supervisord.conf
COPY docker/redis.conf /etc/redis/redis.conf
COPY nginx.conf /etc/nginx/nginx.conf

RUN chmod +x /entrypoint.sh /start-app.sh \
    && mkdir -p \
        /var/lib/postgresql/data \
        /var/lib/redis \
        /data \
        /etc/nginx/certs \
        /app/static \
    && chown -R postgres:postgres /var/lib/postgresql

# --------------------------------------------------
# Ports
# --------------------------------------------------

EXPOSE 80 443 5555 9000 9001 5432 6379

ENTRYPOINT ["/entrypoint.sh"]