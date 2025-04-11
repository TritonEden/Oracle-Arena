#!/bin/bash
set -e

echo "Djano Migrations if needed..."
# Run Django migrations if necessary
if python /app/backend/manage.py showmigrations --plan | grep '\[ \]'; then
    echo "Applying Django migrations..."
    python /app/backend/manage.py migrate
else
    echo "No pending migrations."
fi

cd /app/backend/

echo "Starting Gunicorn (Django backend)..."

gunicorn oracle.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 60 &
GUNICORN_PID=$!

echo "Starting Nginx..."
nginx -g 'daemon off;' &
NGINX_PID=$!

# Trap exit signals to ensure Django server stops gracefully
trap 'echo "Stopping Gunicorn server and Nginx..."; kill $GUNICORN_PID $NGINX_PID; wait $GUNICORN_PID $NGINX_PID' SIGTERM SIGINT




# Store the Gunicorn process ID and wait for it
wait $GUNICORN_PID $NGINX_PID