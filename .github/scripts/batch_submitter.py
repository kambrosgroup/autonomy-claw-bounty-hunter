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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verified_fixer import VerifiedFixer
from typo_scanner import AutoTypoScanner

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
    
    # Apply verified fix
    fix_result = VerifiedFixer.fix_issue(work_dir, title, bounty.get('body', ''))
    
    if not fix_result['success']:
        print(f"   ❌ Fix failed: {fix_result['reason']}")
        return None
    
    if not fix_result['changes']:
        print(f"   ⚠️  No changes made")
        return None
    
    print(f"   ✅ Fix applied: {len(fix_result['changes'])} changes")
    
    # Configure git
    subprocess.run(['git', 'config', 'user.email', 'karlambrosius@outlook.com.au'], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Karl Ambrosius'], cwd=work_dir, capture_output=True)
    
    # Create branch and commit
    branch_name = f"autonomy-fix-{issue_number}"
    subprocess.run(['git', 'checkout', '-b', branch_name], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'add', '-A'], cwd=work_dir, capture_output=True)
    
    changes_summary = '\n'.join([f"- {c}" for c in fix_result['changes'][:10]])
    commit_msg = f"""Fix #{issue_number}: {title[:50]}

{changes_summary}

Fix type: {fix_result['analysis']['fix_type']}
Confidence: {fix_result['analysis']['confidence']:.0%}
Verified: ✅

🤖 Karl Ambrosius
"""
    
    subprocess.run(['git', 'commit', '-m', commit_msg], cwd=work_dir, capture_output=True)
    
    # Fork and push
    run_gh(['repo', 'fork', f'{owner}/{repo}', '--remote=false'], cwd=work_dir)
    
    fork_url = f"https://{USERNAME}:{GITHUB_TOKEN}@github.com/{USERNAME}/{repo}.git"
    subprocess.run(['git', 'remote', 'remove', 'myfork'], cwd=work_dir, capture_output=True)
    subprocess.run(['git', 'remote', 'add', 'myfork', fork_url], cwd=work_dir, capture_output=True)
    
    result = subprocess.run(['git', 'push', '-f', 'myfork', branch_name], cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ Push failed")
        return None
    
    # Create PR
    pr_title = f"Fix #{issue_number}: {title[:60]}"
    pr_body = f"""## Fix for Issue #{issue_number}

### Problem
{title}

### Solution
{changes_summary}

### Verification
- ✅ Fix type: {fix_result['analysis']['fix_type']}
- ✅ Confidence: {fix_result['analysis']['confidence']:.0%}
- ✅ Changes verified

---
*Generated by Karl Ambrosius* 🤖
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
                'fix_result': fix_result
            }
    
    print(f"   ❌ PR creation failed")
    return None

def main():
    print("🚀 Karl Ambrosius Batch PR Submitter")
    print("=" * 70)
    
    # Load opportunities
    opportunities = load_bounty_opportunities()
    print(f"📊 Loaded {len(opportunities)} high-quality opportunities")
    
    if not opportunities:
        print("No opportunities to process")
        return
    
    # Sort by score
    opportunities.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Process top opportunities (limit to avoid rate limits)
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
    
    # Generate summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_opportunities': len(opportunities),
        'processed': max_to_process,
        'submitted': len(results),
        'success_rate': len(results) / max_to_process * 100 if max_to_process > 0 else 0
    }
    
    with open('submissions/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary:")
    print(f"  Total opportunities: {summary['total_opportunities']}")
    print(f"  Processed: {summary['processed']}")
    print(f"  Submitted: {summary['submitted']}")
    print(f"  Success rate: {summary['success_rate']:.1f}%")

if __name__ == "__main__":
    main()
