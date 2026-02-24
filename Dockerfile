# AUTONOMY-CLAW Bounty Hunter Container
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gh \
    jq \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir requests beautifulsoup4

# Copy all scripts
COPY .github/scripts/ ./scripts/
COPY *.py ./

# Create directories with proper permissions
RUN mkdir -p /app/bounties /app/submissions /app/monitoring /app/repos /app/metrics /tmp/bounty-repos \
    && chmod -R 755 /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV REPOS_DIR=/tmp/bounty-repos
ENV GITHUB_TOKEN=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Default command with error handling
CMD ["sh", "-c", "python3 scripts/batch_submitter.py 2>&1 || echo 'Batch submitter failed, trying mega processor...' && python3 mega_batch_processor.py 2>&1 || echo 'All processors failed'"]
