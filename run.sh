#!/bin/bash
# Bounty Hunter Runner

cd /agent/systems/bounty-hunter
python3 hunter.py >> /agent/metrics/bounty_hunter.log 2>&1
