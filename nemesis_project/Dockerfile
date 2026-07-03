FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render sets PORT env variable automatically, but we default to 3001)
ENV PORT=3001
EXPOSE $PORT

# Start FastAPI server with Uvicorn multi-worker scaling
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001} --workers 4"]
