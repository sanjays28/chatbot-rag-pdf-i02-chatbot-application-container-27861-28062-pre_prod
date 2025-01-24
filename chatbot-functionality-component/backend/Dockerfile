FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create directory for PDF storage
RUN mkdir -p /app/storage/pdfs

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Ensure proper permissions for storage directory
RUN chmod -R 755 /app/storage

CMD ["flask", "run", "--host=0.0.0.0"]
