# AUTONOMY-CLAW Bounty Hunter Container - Karl Ambrosius
# Build: docker build -t bounty-hunter .
# Run: docker run -e GITHUB_TOKEN=$TOKEN bounty-hunter

FROM python:3.11-slim

LABEL maintainer="Karl Ambrosius <karlambrosius@outlook.com.au>"
LABEL description="Autonomous bounty hunter for Karl Ambrosius"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python files
COPY *.py ./

# Copy scripts if they exist
RUN mkdir -p scripts
COPY .github/scripts/*.py ./scripts/ 2>/dev/null || echo "No scripts to copy"

# Create necessary directories
RUN mkdir -p /app/bounties /app/submissions /app/monitoring /app/repos /app/metrics /tmp/bounty-repos \
    && chmod -R 755 /app \
    && chmod -R 777 /tmp/bounty-repos

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV REPOS_DIR=/tmp/bounty-repos
ENV GITHUB_TOKEN=""
ENV HOME=/tmp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "print('OK')" || exit 1

# Default command
CMD ["python3", "/app/container_entry.py"]

# Trigger build: Tue Feb 24 06:04:29 PM CST 2026
