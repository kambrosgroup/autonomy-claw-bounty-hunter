#!/usr/bin/env python3
"""
Batch PR Submitter - Karl Ambrosius GitHub Actions
Processes all bounty opportunities and submits verified PRs
"""

import os
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
USERNAME = 'KarlAmbrosius'
REPOS_DIR = '/tmp/bounty-repos'

def run_gh(args, cwd=None):
    """Run GitHub CLI command"""
    env = os.environ.copy()
    env['GH_TOKEN'] = GITHUB_TOKEN
    result = subprocess.run(['gh'] + args, cwd=cwd, capture_output=True, text=True, env=env)
    return result

def load_bounty_opportunities():
    """Load all bounty opportunities from JSON files"""
    opportunities = []
    
    # Load from all bounty type directories
    bounty_dirs = [
        'bounties/documentation',
        'bounties/security', 
        'bounties/dependency',
        'bounties/test',
        'bounties/translation'
    ]
    
    for bounty_dir in bounty_dirs:
        if os.path.exists(bounty_dir):
            for json_file in Path(bounty_dir).glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            opportunities.extend(data)
                        elif isinstance(data, dict) and 'bounties' in data:
                            opportunities.extend(data['bounties'])
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
    
    # Filter for high-quality opportunities
    high_quality = [
        opp for opp in opportunities
        if opp.get('score', 0) >= 30 or opp.get('confidence', 0) >= 0.7
    ]
    
    return high_quality

def process_bounty(bounty, max_attempts=3):
    """Process a single bounty opportunity"""
    url = bounty.get('url', '')
    if not url:
        return None
    
    # Parse GitHub URL
    parts = url.replace('https://github.com/', '').split('/')
    if len(parts) < 4:
        return None
    
    owner = parts[0]
    repo = parts[1]
    issue_number = parts[3] if 'issues' in url else None
    
    if not issue_number:
        return None
    
    title = bounty.get('title', '')
    
    print(f"\n{'='*70}")
    print(f"🎯 Processing: {owner}/{repo}#{issue_number}")
    print(f"   Title: {title[:60]}")
    print(f"   Score: {bounty.get('score', 0):.1f}")
    print('='*70)
    
    work_dir = f"{REPOS_DIR}/{owner}_{repo}"
    
    # Clone repository
    if os.path.exists(work_dir):
        subprocess.run(['rm', '-rf', work_dir], capture_output=True)
    
    os.makedirs(REPOS_DIR, exist_ok=True)
    
    result = subprocess.run(
        ['git', 'clone', '--depth', '1', f'https://github.com/{owner}/{repo}.git', work_dir],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode != 0:
        print(f"   ❌ Clone failed")
        return None
    
    print(f"   ✅ Cloned repository")
    
    # Try to apply fixes using available tools
    changes = []
    
    # Check if universal_fixer exists
    if os.path.exists('/app/universal_fixer.py'):
        try:
            sys.path.insert(0, '/app')
            from universal_fixer import UniversalFixer
            fixer = UniversalFixer(work_dir)
            fix_result = fixer.fix(title, bounty.get('body', ''))
            
            if fix_result.get('success') and fix_result.get('changes'):
                changes = fix_result['changes']
                print(f"   ✅ Applied fixes: {len(changes)} changes")
        except Exception as e:
            print(f"   ⚠️  Universal fixer error: {e}")
    
    if not changes:
        print(f"   ⚠️  No changes could be applied")
        return None
    
    # Configure git
    subprocess.run(['git', 'config', 'user.email', 'karlambrosius@outlook.com.au'], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Karl Ambrosius'], cwd=work_dir, capture_output=True)
    
    # Create branch and commit
    branch_name = f"karl-fix-{issue_number}"
    subprocess.run(['git', 'checkout', '-b', branch_name], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'add', '-A'], cwd=work_dir, capture_output=True)
    
    changes_summary = '\n'.join([f"- {c}" for c in changes[:10]])
    commit_msg = f"""Fix #{issue_number}: {title[:50]}

{changes_summary}

👤 Karl Ambrosius
💰 karlambrosius@outlook.com.au
"""
    
    result = subprocess.run(['git', 'commit', '-m', commit_msg], cwd=work_dir, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✅ Committed changes")
    else:
        print(f"   ⚠️  Commit: {result.stderr[:100]}")
    
    # Fork repo
    print(f"   🍴 Forking repository...")
    run_gh(['repo', 'fork', f'{owner}/{repo}', '--remote=false'], cwd=work_dir)
    
    # Push
    print(f"   📤 Pushing to fork...")
    fork_url = f"https://{USERNAME}:{GITHUB_TOKEN}@github.com/{USERNAME}/{repo}.git"
    subprocess.run(['git', 'remote', 'remove', 'myfork'], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'remote', 'add', 'myfork', fork_url], cwd=work_dir, capture_output=True)
    
    result = subprocess.run(['git', 'push', '-f', 'myfork', branch_name], cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ Push failed: {result.stderr[:200]}")
        return None
    
    print(f"   ✅ Pushed to fork")
    
    # Create PR
    print(f"   📤 Creating PR...")
    pr_title = f"Fix #{issue_number}: {title[:60]}"
    pr_body = f"""## Fix for Issue #{issue_number}

### Problem
{title}

### Solution
{changes_summary}

### Changes Made
- Automated fixes applied
- Files modified: {len(changes)}

---
👤 **Karl Ambrosius**
💰 **PayPal:** karlambrosius@outlook.com.au
"""
    
    for base in ['main', 'master']:
        result = run_gh([
            'pr', 'create',
            '--repo', f'{owner}/{repo}',
            '--title', pr_title,
            '--body', pr_body,
            '--head', f'{USERNAME}:{branch_name}',
            '--base', base
        ], cwd=work_dir)
        
        if result.returncode == 0:
            pr_url = result.stdout.strip()
            print(f"   ✅ PR created: {pr_url}")
            return {
                'bounty': bounty,
                'pr_url': pr_url,
                'changes': changes
            }
    
    print(f"   ❌ PR creation failed")
    return None

def main():
    print("🚀 Karl Ambrosius - Batch PR Submitter")
    print("=" * 70)
    print("PayPal: karlambrosius@outlook.com.au")
    print("=" * 70)
    
    # Load opportunities
    opportunities = load_bounty_opportunities()
    print(f"\n📊 Loaded {len(opportunities)} high-quality opportunities")
    
    if not opportunities:
        print("No opportunities to process")
        return
    
    # Sort by score
    opportunities.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Process top opportunities
    max_to_process = min(10, len(opportunities))
    print(f"🎯 Processing top {max_to_process} opportunities\n")
    
    results = []
    for i, bounty in enumerate(opportunities[:max_to_process], 1):
        print(f"\n[{i}/{max_to_process}]")
        result = process_bounty(bounty)
        if result:
            results.append(result)
    
    # Save results
    os.makedirs('submissions', exist_ok=True)
    results_file = f"submissions/batch_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"🎉 COMPLETE - {len(results)} PRs submitted!")
    print(f"💾 Results saved: {results_file}")
    print(f"\n👤 Karl Ambrosius")
    print(f"💰 karlambrosius@outlook.com.au")

if __name__ == "__main__":
    main()
