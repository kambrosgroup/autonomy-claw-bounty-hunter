#!/bin/bash
# AUTONOMY-CLAW Bounty Hunter Runner - Enhanced
# Runs every 6 hours for maximum bounty hunting

cd /agent/systems/bounty-hunter

# Run enhanced bounty hunter
python3 enhanced_hunter.py >> /agent/metrics/bounty_hunter.log 2>&1

# Submit any ready PRs
python3 fix_and_submit_v2.py >> /agent/metrics/pr_submissions.log 2>&1

# Monitor existing PRs
python3 pr_monitor.py >> /agent/metrics/pr_monitor.log 2>&1

echo "[$(date)] Bounty cycle complete" >> /agent/metrics/cron.log
