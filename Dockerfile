# Use Alpine OS as the base image
FROM alpine:3.18

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/miniforge3/bin:$PATH"

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

# Install glibc on Alpine Linux
RUN curl -LO https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r0/glibc-2.35-r0.apk && \
    curl -LO https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r0/glibc-bin-2.35-r0.apk && \
    curl -LO https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r0/glibc-i18n-2.35-r0.apk && \
    apk add --no-cache glibc-2.35-r0.apk glibc-bin-2.35-r0.apk glibc-i18n-2.35-r0.apk && \
    /usr/glibc-compat/bin/localedef -i en_US -f UTF-8 en_US.UTF-8 && \
    rm -rf /var/cache/apk/* && \
    rm -rf glibc-*.apk

# Install Miniforge (for Conda environment management)
RUN curl -LO https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh && \
    bash Miniforge3-Linux-x86_64.sh -b -p /root/miniforge3 && \
    rm Miniforge3-Linux-x86_64.sh && \
    conda init bash

# Install Conda packages (you can modify based on your specific needs)
RUN conda install -y \
    python=3.10 \
    && conda clean --all -f -y

# Install Python packages (Django, Django Rest Framework, etc.)
RUN pip install --upgrade pip && \
    pip install \
    django==4.2 \
    djangorestframework \
    psycopg2-binary

# Install Node.js packages (Next.js, etc.)
RUN npm install -g next react react-dom

# Create working directory for the app
WORKDIR /app

# Copy the rest of the project into the container
COPY . /app

# Copy Nginx configuration file
COPY ./backend/nginx/conf/nginx.conf /etc/nginx/nginx.conf

# Expose the required ports for Django, Next.js, and Nginx
EXPOSE 8000 3000 80

# Start Nginx, Django, and Next.js
CMD ["sh", "-c", "nginx && python manage.py runserver 0.0.0.0:8000 && npm run dev"]
