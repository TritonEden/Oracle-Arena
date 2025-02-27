#!/bin/bash
set -e

echo "Ensuring /var/lib/postgresql/data is owned by postgres..."
chown -R postgres:postgres /var/lib/postgresql

# Initialize PostgreSQL data directory if missing
if [ ! -d "/var/lib/postgresql/data/base" ]; then
    echo "Initializing PostgreSQL data directory..."
    su - postgres -c "initdb -D /var/lib/postgresql/data"
fi

# Start PostgreSQL in the background
echo "Starting PostgreSQL..."
su - postgres -c "pg_ctl -D /var/lib/postgresql/data -l /var/lib/postgresql/logfile start"

# Wait for PostgreSQL to be ready before proceeding
echo "Waiting for PostgreSQL to be ready..."
until psql -U postgres -c "SELECT 1" &>/dev/null; do
    sleep 1
done

# Create user/db if they don't exist yet
echo "Ensuring PostgreSQL user/database..."
psql -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_USER'" | grep -q 1 || \
  psql -U postgres -c "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"

psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'" | grep -q 1 || \
  psql -U postgres -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

echo "Checking if tables exist..."
TABLE_EXISTS=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='teams';")

# Create database tables if they don't exist yet
if [ -z "$TABLE_EXISTS" ]; then
    echo "Running table creation script..."
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /app/backend/database/oracle_table_create.sql
else
    echo "Tables already exist, skipping creation."
fi

# Run Django migrations if necessary
if python /app/backend/manage.py showmigrations --plan | grep '\[ \]'; then
    echo "Applying Django migrations..."
    python /app/backend/manage.py migrate
else
    echo "No pending migrations."
fi

# Trap exit signals to ensure Django server stops gracefully
trap 'echo "Stopping Django server and Nginx..."; kill $DJANGO_PID $NGINX_PID; wait $DJANGO_PID $NGINX_PID' SIGTERM SIGINT

echo "Starting Django dev server..."
python /app/backend/manage.py runserver 0.0.0.0:8000 &

echo "Starting Nginx..."
nginx -g 'daemon off;' &

# Store the Django process ID and wait for it
DJANGO_PID=$!
wait $DJANGO_PID $NGINX_PID
