#!/bin/bash

set -e

echo "Starting e-commerce container..."

# --------------------------------------------------
# Create directories
# --------------------------------------------------

mkdir -p \
    "$PGDATA" \
    /var/lib/redis \
    /data \
    /etc/nginx/certs \
    /run

chown -R postgres:postgres "$PGDATA"

# --------------------------------------------------
# Initialize PostgreSQL if necessary
# --------------------------------------------------

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL..."

    su -s /bin/bash postgres -c \
        "/usr/lib/postgresql/16/bin/initdb \
        -D '$PGDATA' \
        --auth-local=trust \
        --auth-host=trust"
fi

# --------------------------------------------------
# Generate self-signed SSL certificate
# --------------------------------------------------

if [ ! -s /etc/nginx/certs/cert.crt ]; then
    echo "Generating SSL certificate..."

    openssl req -x509 -nodes -newkey rsa:2048 \
        -keyout /etc/nginx/certs/cert.key \
        -out /etc/nginx/certs/cert.crt \
        -days 3650 \
        -subj "/C=UA/ST=Dnipro/L=Dnipro/O=Hillel/OU=lector/CN=localhost"
fi

# --------------------------------------------------
# Start all services
# --------------------------------------------------

echo "Starting Supervisor..."

exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf