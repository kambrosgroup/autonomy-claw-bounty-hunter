# GitHub Actions Automation Suite

**AUTONOMY-CLAW - Complete GitHub Automation for 302 Bounty Opportunities**

---

## 🚀 Quick Start

```bash
cd /agent/systems/bounty-hunter
./setup-github-actions.sh
```

This will:
1. ✅ Check prerequisites (GitHub CLI)
2. ✅ Set up workflow files
3. ✅ Configure secrets
4. ✅ Push to GitHub
5. ✅ Enable automation

---

## 📁 Workflow Files

### 1. `bounty-hunter.yml` - Main Workflow
**Triggers:** Every 6 hours + Manual

**Jobs:**
- **documentation-bounties**: Find and process documentation issues
- **security-bounties**: Find security vulnerabilities
- **dependency-bounties**: Find outdated dependencies
- **test-bounties**: Find test coverage gaps
- **translation-bounties**: Find i18n opportunities
- **submit-prs**: Process all findings and submit verified PRs
- **monitor-prs**: Check status of existing PRs
- **daily-report**: Generate and post daily summary

**Usage:**
```bash
# Run all bounty types
gh workflow run bounty-hunter.yml

# Run specific type
gh workflow run bounty-hunter.yml -f bounty_type=documentation
```

### 2. `container-deploy.yml` - Container Build
**Triggers:** Push to main + Manual

**Features:**
- Builds Docker image
- Pushes to GitHub Container Registry (GHCR)
- Generates SBOM
- Creates deployment status

**Image:**
```
ghcr.io/kambrosgroup/bounty-hunter:latest
```

### 3. `auto-respond.yml` - Comment Automation
**Triggers:** Issue/PR comments

**Features:**
- Auto-responds to maintainer comments
- Context-aware responses
- Professional tone

---

## 🐳 Container Usage

### Pull and Run
```bash
# Pull image
docker pull ghcr.io/kambrosgroup/bounty-hunter:latest

# Run with your token
docker run -e GITHUB_TOKEN=ghp_xxx ghcr.io/kambrosgroup/bounty-hunter:latest
```

### Build Locally
```bash
docker build -t bounty-hunter .
docker run -e GITHUB_TOKEN=ghp_xxx bounty-hunter
```

---

## 📊 Automation Schedule

```
Every 6 hours:
├── 00:00 - Run all bounty hunters
├── 00:30 - Submit verified PRs
├── 01:00 - Monitor existing PRs
├── 01:30 - Generate report
└── Post results as GitHub Issue

On PR comment:
└── Auto-respond within seconds

On push to main:
└── Build and deploy container
```

---

## 🔐 Required Secrets

### Automatic (provided by GitHub)
- `GITHUB_TOKEN` - Automatically provided

### Optional (for enhanced features)
- `PAYPAL_CLIENT_ID` - For SaaS subscriptions
- `PAYPAL_SECRET` - For SaaS subscriptions

### Set Secrets
```bash
gh secret set PAYPAL_CLIENT_ID
gh secret set PAYPAL_SECRET
```

---

## 📈 Monitoring

### View Results
1. **Actions Tab**: See workflow runs
2. **Issues Tab**: Daily reports posted as issues
3. **Artifacts**: Download bounty data and PR submissions
4. **Packages**: Container images in GHCR

### Artifacts
- `documentation-bounties/*.json`
- `security-bounties/*.json`
- `pr-submissions/*.json`
- `daily-report/*.md`

---

## 🎯 Processing 302 Opportunities

### Batch Processing
The system processes opportunities in batches:
- **Per run**: Up to 10 high-quality bounties
- **Per day**: Up to 40 bounties (4 runs × 10)
- **Per week**: Up to 280 bounties

### Prioritization
Bounties are sorted by:
1. Score (bounty amount × fixability)
2. Confidence (fix success probability)
3. Recency (newer issues prioritized)

### Verification
Every fix is verified before PR submission:
- ✅ Specific typo: Confirmed no longer exists
- ✅ CHANGELOG: File created
- ✅ README: Changes applied
- ✅ Formatting: Files modified

---

## 🛠️ Scripts

### `batch_submitter.py`
Processes all bounty opportunities and submits verified PRs.

### `pr_monitor.py`
Monitors existing PRs for status changes and maintainer feedback.

### `generate_report.py`
Generates daily summary of all activities.

---

## 💰 Revenue Tracking

PRs are tracked automatically:
- Submissions: `submissions/*.json`
- Status updates: `monitoring/*.json`
- Daily summaries: `reports/*.md`
- Merged PRs: Tracked via GitHub API

---

## 🔧 Troubleshooting

### Workflow Not Running
```bash
# Check if Actions are enabled
gh repo view --json url
# Go to Actions tab and enable
```

### Rate Limiting
The workflow respects GitHub API rate limits:
- Uses authenticated requests (5000/hour)
- Processes max 10 bounties per run
- Adds delays between requests

### Failed PRs
Failed submissions are logged:
```bash
cat submissions/batch_*.json
```

---

## 📚 Documentation

- `GITHUB_APP.md` - GitHub App configuration
- `TEST_RESULTS.md` - Verified fixer test results
- `BOUNTY_SUITE.md` - Bounty hunter documentation

---

**AUTONOMY-CLAW is now fully automated via GitHub Actions!**
