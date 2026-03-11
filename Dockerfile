# Use Python 3.10 to match Ray image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app/src

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure data and logs directories exist
RUN mkdir -p data/rl_training Logs

# Expose the API port
EXPOSE 8000

# Default command runs the CLI
# In docker-compose we will override this for the API service
CMD ["python", "src/graph_cortex/interfaces/cli/main.py"]
