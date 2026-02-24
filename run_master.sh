#!/bin/bash
# AUTONOMY-CLAW Master Bounty Hunter
# Runs all bounty hunting modules

echo "🚀 AUTONOMY-CLAW Master Bounty Hunter"
echo "======================================"
echo "Started: $(date)"
echo ""

BASE_DIR="/agent/systems/bounty-hunter"

# 1. Documentation Bounties (Original)
echo "📚 Running Documentation Bounty Hunter..."
python3 $BASE_DIR/enhanced_hunter.py >> /agent/metrics/bounty_hunter.log 2>&1
python3 $BASE_DIR/fix_and_submit_v2.py >> /agent/metrics/pr_submissions.log 2>&1

# 2. Security Bounties
echo "🔒 Running Security Bounty Hunter..."
python3 $BASE_DIR/security/hunter.py >> /agent/metrics/security_bounty.log 2>&1

# 3. Dependency Updates
echo "📦 Running Dependency Bounty Hunter..."
python3 $BASE_DIR/dependency/hunter.py >> /agent/metrics/dependency_bounty.log 2>&1

# 4. Test Coverage
echo "🧪 Running Test Coverage Bounty Hunter..."
python3 $BASE_DIR/test/hunter.py >> /agent/metrics/test_bounty.log 2>&1

# 5. Translation/Localization
echo "🌐 Running Translation Bounty Hunter..."
python3 $BASE_DIR/translation/hunter.py >> /agent/metrics/translation_bounty.log 2>&1

# 6. Monitor existing PRs
echo "👁️  Monitoring existing PRs..."
python3 $BASE_DIR/pr_monitor.py >> /agent/metrics/pr_monitor.log 2>&1

echo ""
echo "======================================"
echo "Completed: $(date)"
echo "All bounty hunters finished."
