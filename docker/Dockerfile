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

# Install Prefect and common data tools
RUN pip install --no-cache-dir \
    prefect==2.14.21 \
    pandas==2.1.4 \
    boto3==1.34.0 \
    requests==2.31.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9

# Copy example flows
COPY docker/flows/ /app/flows/
COPY docker/prefect-entrypoint.sh /app/prefect-entrypoint.sh

# Make scripts executable
RUN chmod +x /app/prefect-entrypoint.sh

# Change ownership to prefect user
RUN chown -R prefect:prefect /app

# Switch to prefect user
USER prefect

# Expose Prefect UI port
EXPOSE 4200

# Default command
CMD ["/app/prefect-entrypoint.sh"]

