FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install system dependencies if any additional ones are needed
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

# Ensure playwright browsers are fully installed just in case
RUN playwright install chromium

# The command will be overridden by render.yaml startCommand
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
