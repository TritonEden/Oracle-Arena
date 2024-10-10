# Use Alpine OS as the base image
FROM alpine:3.18

# Set environment variables
ENV PYTHONUNBUFFERED=1

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
    postgresql-dev \
    nginx

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

# Expose the required ports for Django, Next.js, and Nginx (if needed later)
EXPOSE 8000 3000 80

# Set the default command to run Bash
CMD ["/bin/bash"]
