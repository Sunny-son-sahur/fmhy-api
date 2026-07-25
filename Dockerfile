FROM python:3.11-slim

WORKDIR /app

# Install git for pulling wiki content
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make scripts executable
RUN chmod +x run.sh update.sh setup-cron.sh

# Parse and setup database
RUN python3 parser.py && python3 database.py

EXPOSE 8000

CMD ["python3", "main.py"]
