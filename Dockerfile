# Use Python 3.12 slim image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn celery redis pydantic-settings python-dotenv tenacity

# Pre-download Whisper base model
RUN python3 -c "import whisper; whisper.load_model('base')"

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p downloads processed output jobs

# Expose API port
EXPOSE 8080

# The default command will be overridden by docker-compose
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
