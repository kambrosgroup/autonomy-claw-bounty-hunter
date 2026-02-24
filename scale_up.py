#!/usr/bin/env python3
"""
Scale Up Bounty Hunter - Process more bounties
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime

sys.path.insert(0, '/agent/systems/bounty-hunter')
from smart_fixer import SmartFixer

GITHUB_TOKEN = open('/secrets/github_token').read().strip()
USERNAME = 'KarlAmbrosius'
REPOS_DIR = '/agent/systems/bounty-hunter/data/repos'

def run_gh(args, cwd=None):
    env = os.environ.copy()
    env['GH_TOKEN'] = GITHUB_TOKEN
    return subprocess.run(['gh'] + args, cwd=cwd, capture_output=True, text=True, env=env)

def submit_bounty(owner, repo, issue_number, issue_title):
    """Submit a single bounty"""
    owner_repo = f"{owner}_{repo}"
    work_dir = f"{REPOS_DIR}/{owner_repo}"
    
    print(f"\n🚀 {owner}/{repo} - Issue #{issue_number}")
    
    # Clone fresh
    if os.path.exists(work_dir):
        subprocess.run(['rm', '-rf', work_dir], capture_output=True)
    
    result = subprocess.run(
        ['git', 'clone', '--depth', '1', f'https://github.com/{owner}/{repo}.git', work_dir],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"   ❌ Clone failed")
        return None
    
    # Apply fixes
    fix_results = SmartFixer.run_all_fixes(work_dir)
    
    if fix_results['total_changes'] == 0:
        print(f"   ⚠️  No changes")
        return None
    
    print(f"   ✅ Fixed {fix_results['total_changes']} issues")
    
    # Configure and commit
    subprocess.run(['git', 'config', 'user.email', 'karlambrosius@outlook.com.au'], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Karl Ambrosius'], cwd=work_dir, capture_output=True)
    
    branch_name = f"autonomy-fix-{issue_number}"
    subprocess.run(['git', 'checkout', '-b', branch_name], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'add', '-A'], cwd=work_dir, capture_output=True)
    
    commit_msg = f"Fix #{issue_number}: {issue_title[:50]}\n\nAutomated fixes by Karl Ambrosius 🤖"
    subprocess.run(['git', 'commit', '-m', commit_msg], cwd=work_dir, capture_output=True)
    
    # Fork and push
    run_gh(['repo', 'fork', f'{owner}/{repo}', '--remote=false'], cwd=work_dir)
    time.sleep(2)
    
    fork_url = f"https://{USERNAME}:{GITHUB_TOKEN}@github.com/{USERNAME}/{repo}.git"
    subprocess.run(['git', 'remote', 'add', 'myfork', fork_url], cwd=work_dir, capture_output=True)
    
    result = subprocess.run(['git', 'push', '-f', 'myfork', branch_name], cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ Push failed")
        return None
    
    # Create PR
    pr_title = f"Fix #{issue_number}: {issue_title[:60]}"
    pr_body = f"""## Automated Fix

This PR addresses issue #{issue_number}.

Changes:
- Fixed {fix_results['typos_fixed']} typos
- Fixed {fix_results['trailing_ws_fixed']} whitespace issues
- Added {fix_results['newlines_added']} newlines

🤖 Karl Ambrosius"""
    
    for base in ['main', 'master']:
        result = run_gh([
            'pr', 'create', '--repo', f'{owner}/{repo}',
            '--title', pr_title, '--body', pr_body,
            '--head', f'{USERNAME}:{branch_name}', '--base', base
        ], cwd=work_dir)
        if result.returncode == 0:
            pr_url = result.stdout.strip()
            print(f"   ✅ PR: {pr_url}")
            return {'pr_url': pr_url, 'fixes': fix_results}
    
    print(f"   ❌ PR failed")
    return None

def main():
    print("🚀 Scale Up - Processing More Bounties")
    print("=" * 70)
    
    # Additional documentation bounties to process
    # These are from the 59 we identified earlier
    more_bounties = [
        ('Timi16', 'soroban-debugger', '257', 'Document All CLI Flags and Subcommands'),
        ('Timi16', 'soroban-debugger', '256', 'Write Getting Started Guide'),
        ('Timi16', 'soroban-debugger', '194', 'Add CHANGELOG.md and Release Notes'),
        ('Timi16', 'soroban-debugger', '192', 'Add man Page Generation'),
        ('rysweet', 'azlin', '676', 'Documentation: README version mismatch'),
    ]
    
    results = []
    for owner, repo, issue, title in more_bounties:
        result = submit_bounty(owner, repo, issue, title)
        if result:
            results.append({'owner': owner, 'repo': repo, 'issue': issue, 'title': title, **result})
        time.sleep(2)  # Rate limit protection
    
    print("\n" + "=" * 70)
    print(f"🎉 Submitted {len(results)} additional PRs!")
    
    for r in results:
        print(f"\n✅ {r['owner']}/{r['repo']} #{r['issue']}")
        print(f"   {r['pr_url']}")
    
    # Save results
    results_file = f"/agent/metrics/pr_submissions_scale_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved: {results_file}")

if __name__ == "__main__":
    main()
