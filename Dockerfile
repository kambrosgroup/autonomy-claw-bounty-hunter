# AUTONOMY-CLAW Bounty Hunter Container
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gh \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bounty hunter code
COPY .github/scripts/ ./scripts/
COPY *.py ./

# Create directories
RUN mkdir -p /app/bounties /app/submissions /app/monitoring /app/repos

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GITHUB_TOKEN=""
ENV REPOS_DIR=/app/repos

# Default command
CMD ["python3", "scripts/batch_submitter.py"]
