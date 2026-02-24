#!/bin/bash
# Test container execution locally

echo "=========================================="
echo "Testing Container Execution"
echo "=========================================="
echo ""

# Set test environment
export GITHUB_TOKEN=$(cat /secrets/github_token 2>/dev/null || echo "test-token")
export REPOS_DIR=/tmp/test-bounty-repos
export HOME=/tmp

echo "Environment:"
echo "  GITHUB_TOKEN: ${GITHUB_TOKEN:0:10}..."
echo "  REPOS_DIR: $REPOS_DIR"
echo "  HOME: $HOME"
echo ""

# Create test directories
mkdir -p /app/scripts /app/bounties /app/submissions $REPOS_DIR

# Copy scripts to /app (simulating container)
cp /agent/systems/bounty-hunter/*.py /app/ 2>/dev/null || echo "Copy failed"
cp /agent/systems/bounty-hunter/.github/scripts/*.py /app/scripts/ 2>/dev/null || echo "Scripts copy failed"

echo "Files in /app:"
ls -la /app/
echo ""

echo "Files in /app/scripts:"
ls -la /app/scripts/ 2>/dev/null || echo "No scripts directory"
echo ""

# Test Python imports
echo "Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, '/app')
try:
    from universal_fixer import UniversalFixer
    print('✅ UniversalFixer imported')
except Exception as e:
    print(f'❌ UniversalFixer import failed: {e}')

try:
    from typo_scanner import AutoTypoScanner
    print('✅ AutoTypoScanner imported')
except Exception as e:
    print(f'❌ AutoTypoScanner import failed: {e}')
"

echo ""
echo "=========================================="
echo "Container test complete"
echo "=========================================="
