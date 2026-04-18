# Dockerfile for HELEN OS — Multi-Model Deployment

FROM python:3.10-slim

# Set working directory
WORKDIR /helen

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy HELEN OS source
COPY helen_*.py ./
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create configuration directory
RUN mkdir -p /root/.helen_os

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Default command: start CLI interface
CMD ["python", "-m", "helen_unified_interface_v1"]

# Alternative: run as API server (uncomment to use)
# CMD ["python", "-m", "helen_api_server_v1"]
