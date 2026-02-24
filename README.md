# GitHub Bounty Hunter - AUTONOMY-CLAW System 4

## Overview
Automated system that finds GitHub issues with bounties, attempts intelligent fixes, and prepares pull requests.

## How It Works

### 1. Discovery Phase
- Searches GitHub for issues labeled: `bounty`, `reward`, `good first issue`
- Looks for bounty amounts in titles and descriptions
- Scores issues by: bounty amount, difficulty, recency

### 2. Analysis Phase
- Clones target repositories
- Analyzes issue for auto-fix potential:
  - **Typos** - High confidence, easy fixes
  - **Documentation** - README updates, link fixes
  - **Linting** - Code style, formatting
  - **Dependencies** - Version bumps (manual review needed)

### 3. Fix Phase
- `SmartFixer` module handles common fixes:
  - Common typo corrections (recieve→receive, etc.)
  - Trailing whitespace removal
  - Missing newline fixes
  - Language-specific formatters (black, eslint, prettier)

### 4. Submission Phase
- Creates feature branch
- Commits changes with descriptive message
- Prepares for PR creation (requires GitHub token for push)

## Files

| File | Purpose |
|------|---------|
| `hunter.py` | Main bounty hunting logic |
| `smart_fixer.py` | Intelligent code fixing |
| `run.sh` | Execution wrapper |
| `data/state.json` | Tracked bounties and attempts |

## Usage

### Manual Run
```bash
cd /agent/systems/bounty-hunter
python3 hunter.py
```

### With GitHub Token (Full Functionality)
```bash
export GITHUB_TOKEN=your_token_here
python3 hunter.py
```

### Cron Schedule
Runs twice daily (every 12 hours)

## Bounty Sources

The hunter searches for:
- Issues labeled `bounty`, `reward`, `good first issue`
- Titles containing `$` amounts
- Descriptions mentioning "bounty", "reward", "fix"
- Platforms: GitHub native, Gitcoin, Algora, etc.

## Current Status

- ✅ Issue discovery: Working (public API)
- ✅ Repository cloning: Working
- ✅ Smart fixing: Working
- ⏳ PR creation: Needs GitHub token with push access
- ⏳ Bounty claiming: Manual (platform-specific)

## Revenue Potential

| Fix Type | Avg Bounty | Success Rate | Est. Monthly |
|----------|------------|--------------|--------------|
| Typos/Docs | $10-50 | 30% | $50-150 |
| Bug Fixes | $100-500 | 10% | $100-300 |
| Features | $500+ | 5% | $100-500 |
| **Total** | | | **$250-950/month** |

## Next Steps

1. **Get GitHub Token** - Enable PR creation
   - Create at: https://github.com/settings/tokens
   - Scopes needed: `repo`, `workflow`
   - Save to: `/secrets/github_token`

2. **Fork Strategy** - For repos without write access
   - Auto-fork target repos
   - Push to fork, create PR upstream

3. **Platform Integration** - Direct bounty claiming
   - Gitcoin API
   - Algora API
   - GitHub Sponsors

