# Prefect Data Orchestration Environment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PREFECT_API_URL=http://localhost:4200/api

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create prefect user
RUN useradd -m -s /bin/bash prefect

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    prefect==2.14.21 \
    pandas==2.1.4 \
    requests==2.31.0 \
    pyspark==3.5.0 \
    delta-spark==3.0.0 \
    pyarrow==14.0.1 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9

# Fix griffe version conflict (Prefect installs 1.8.0 but needs 0.38.1)
RUN pip install --no-cache-dir griffe==0.38.1

# Copy flows from parent directory (using correct Docker build context)
COPY flows/ /app/flows/
COPY docker/prefect-entrypoint.sh /app/prefect-entrypoint.sh
COPY docker/s3/ /app/s3/

# Make scripts executable
RUN chmod +x /app/prefect-entrypoint.sh


# Corrige permissões para o diretório do UI do Prefect Server
RUN mkdir -p /usr/local/lib/python3.11/site-packages/prefect/server/ui_build \
    && chmod -R 777 /usr/local/lib/python3.11/site-packages/prefect/server/ui_build \
    && chown -R prefect:prefect /app

# Switch to prefect user
USER prefect

# Expose Prefect UI port
EXPOSE 4200

# Default command
CMD ["/app/prefect-entrypoint.sh"]

