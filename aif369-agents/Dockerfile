FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agents/ agents/
COPY tests/ tests/
COPY db/ db/
COPY *.py ./

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/master/health || exit 1

# Run FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
