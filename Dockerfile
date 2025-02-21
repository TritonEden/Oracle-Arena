# Use Alpine OS as the base image
FROM alpine:3.18

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV POSTGRES_DB=oracle_db
ENV POSTGRES_USER=oracle_admin

# Install essential dependencies including Bash
RUN apk update && apk add --no-cache \
    bash \
    build-base \
    linux-headers \
    libffi-dev \
    openssl-dev \
    bzip2-dev \
    zlib-dev \
    xz-dev \
    readline-dev \
    sqlite-dev \
    git \
    curl \
    make \
    gcc \
    g++ \
    libc-dev \
    ca-certificates \
    nodejs \
    npm \
    yarn \
    python3 \
    py3-pip \
    python3-dev \
    postgresql \
    postgresql-dev \
    nginx \
    vim

# Upgrade pip and install Django 5.1 (development version)
RUN pip install --upgrade pip && \
    pip install \
    django==5.1 \
    djangorestframework \
    psycopg2-binary

# Install Node.js packages (Next.js, React, etc.)
RUN npm install -g next react react-dom

# Create working directory for the app
WORKDIR /app

# Copy the rest of the project into the container
COPY . /app

# Copy Nginx configuration file
COPY ./backend/nginx/conf/nginx.conf /etc/nginx/nginx.conf

#backend setup

# Install Python dependencies from the requirements.txt file

RUN pip install -r /app/backend/requirements.txt

#Include frontend setup later -- use npm i
RUN cd /app/frontend && npm install && cd ..

# ## Initialize PostgreSQL data directory
# RUN mkdir -p /var/lib/postgresql/data && \
#     chown postgres:postgres /var/lib/postgresql/data && \
#     su - postgres -c "initdb -D /var/lib/postgresql/data"

# # Copy the SQL file to initialize the database
# COPY ./backend/oracle_table_create.sql /tmp/oracle_table_create.sql

# # Start Postgres, create database and user then run the SQL file to create the tables
# RUN su - postgres -c "pg_ctl -D /var/lib/postgresql/data start" && \
#     sleep 5 && \
#     psql -U postgres -c "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';" && \
#     psql -U postgres -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;" && \
#     psql -U $POSTGRES_USER -d $POSTGRES_DB -f /tmp/oracle_table_create.sql && \
#     rm /tmp/oracle_table_create.sql


# Ensure /var/lib/postgresql/data exists and is owned by postgres
RUN mkdir -p /var/lib/postgresql/data && \
    chown -R postgres:postgres /var/lib/postgresql


RUN mkdir -p /run/postgresql \
    && chown -R postgres:postgres /run/postgresql \
    && chmod 775 /run/postgresql

# Allow entrypoint script to be executable
RUN chmod +x /app/backend/database/entrypoint.sh


# Expose the required ports for Django, Next.js, and Nginx (if needed later)
EXPOSE 8000 3000 80

# # Run Nginx in the background
# RUN nginx -g 'daemon off;' &

# # Run the python server

# RUN python backend/manage.py runserver &

# Set the default command to run Bash
#CMD ["/bin/bash"]

# Entrypoint script to start database 
ENTRYPOINT ["/app/backend/database/entrypoint.sh"]
