# AUTONOMY-CLAW GitHub App

This directory contains configuration for the AUTONOMY-CLAW GitHub App.

## Installation

1. Go to Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Fill in the manifest from `app-manifest.json`
4. Install on your repositories

## Permissions Required

### Repository Permissions
- **Pull requests**: Read & Write
- **Issues**: Read & Write
- **Contents**: Read & Write
- **Actions**: Read & Write
- **Metadata**: Read

### Organization Permissions
- **Members**: Read

## Events Subscribed
- Pull request
- Pull request review
- Issues
- Issue comment
- Push

## Features

### Automated Bounty Hunting
- Scans 302+ bounty opportunities
- Applies verified fixes
- Submits PRs automatically
- Monitors PR status
- Auto-responds to reviews

### Supported Fix Types
1. **Documentation**: Typos, formatting, CHANGELOGs
2. **Security**: Vulnerability patches
3. **Dependencies**: Version updates
4. **Testing**: Coverage improvements
5. **Translation**: i18n support

### Workflow
```
Every 6 hours:
├── Scan for bounties
├── Analyze issues
├── Apply verified fixes
├── Submit PRs
├── Monitor existing PRs
└── Generate reports
```

## Environment Variables

```bash
GITHUB_TOKEN=ghp_xxx
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----
PAYPAL_CLIENT_ID=xxx
PAYPAL_SECRET=xxx
```

## Usage

### Manual Trigger
```bash
gh workflow run bounty-hunter.yml
```

### With Parameters
```bash
gh workflow run bounty-hunter.yml -f bounty_type=documentation
```

### Container
```bash
docker pull ghcr.io/kambrosgroup/bounty-hunter:latest
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN ghcr.io/kambrosgroup/bounty-hunter:latest
```

## Monitoring

View results:
- Actions tab: Workflow runs
- Issues tab: Daily reports
- Artifacts: Bounty data and PR submissions

## Revenue Tracking

PRs are tracked in:
- `submissions/*.json` - Submitted PRs
- `monitoring/*.json` - PR status updates
- `reports/*.md` - Daily summaries

---
*AUTONOMY-CLAW - Autonomous Bounty Hunter*
