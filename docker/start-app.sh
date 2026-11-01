#!/bin/bash

set -e

APP_TYPE="$1"

# --------------------------------------------------
# Wait for PostgreSQL
# --------------------------------------------------

wait_for_postgres() {
    echo "Waiting for PostgreSQL..."

    until pg_isready -h 127.0.0.1 -p 5432 -U postgres; do
        sleep 2
    done

    echo "PostgreSQL is ready."
}

# --------------------------------------------------
# Initialize database
# --------------------------------------------------

initialize_database() {
    echo "Creating database and user if necessary..."

    psql -h 127.0.0.1 -U postgres -d postgres \
        -v ON_ERROR_STOP=1 \
        -v db_user="$DB_USER" \
        -v db_password="$DB_PASSWORD" \
        -v db_name="$DB_NAME" <<'SQL'

SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L',
    :'db_user',
    :'db_password'
)
WHERE NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = :'db_user'
)
\gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN PASSWORD %L',
    :'db_user',
    :'db_password'
)
\gexec

SELECT format(
    'CREATE DATABASE %I OWNER %I',
    :'db_name',
    :'db_user'
)
WHERE NOT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = :'db_name'
)
\gexec

SQL
}

# --------------------------------------------------
# Primary Django application
# --------------------------------------------------

if [ "$APP_TYPE" = "primary" ]; then

    wait_for_postgres

    initialize_database

    echo "Running Django migrations..."

    python manage.py migrate --noinput

    touch /tmp/migrations.done

    echo "Starting Django app on port 8000..."

    exec uvicorn e_commerce.asgi:application \
        --host 0.0.0.0 \
        --port 8000

fi

# --------------------------------------------------
# Duplicate Django application
# --------------------------------------------------

if [ "$APP_TYPE" = "duplicate" ]; then

    echo "Waiting for Django migrations..."

    until [ -f /tmp/migrations.done ]; do
        sleep 2
    done

    echo "Starting Django duplicate app on port 8001..."

    exec uvicorn e_commerce.asgi:application \
        --host 0.0.0.0 \
        --port 8001

fi

echo "Unknown application type: $APP_TYPE"

exit 1