#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_PORT" ]; then
    echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
    until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
        sleep 0.5
    done
fi

if [ "${MIGRATE_ON_START:-true}" = "true" ]; then
    python manage.py migrate --noinput
fi

exec "$@"
