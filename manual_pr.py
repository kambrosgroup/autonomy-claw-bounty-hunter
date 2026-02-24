#!/usr/bin/env python3
"""
Manual Bounty Hunter - Create PRs step by step with user guidance
"""

import os
import subprocess
import json
from datetime import datetime

GITHUB_TOKEN = open('/secrets/github_token').read().strip()
USERNAME = 'KarlAmbrosius'

def read_state():
    state_file = '/agent/systems/bounty-hunter/data/state.json'
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return {'bounties_found': [], 'bounties_attempted': []}

def main():
    print("🎯 Manual Bounty PR Creator")
    print("=" * 70)
    
    state = read_state()
    bounties = state.get('bounties_found', [])
    
    if not bounties:
        print("\n⚠️  No bounties found yet. Run enhanced_hunter.py first.")
        return
    
    # Filter for high-quality documentation fixes
    good_bounties = [
        b for b in bounties 
        if b.get('score', 0) >= 30 
        and any(t in str(b.get('labels', [])) for t in ['documentation', 'docs', 'good first issue'])
    ]
    
    print(f"\n📊 Found {len(good_bounties)} good documentation bounties")
    print("\nTop opportunities:")
    print("-" * 70)
    
    for i, b in enumerate(good_bounties[:10], 1):
        print(f"\n{i}. {b['title'][:60]}")
        print(f"   URL: {b['url']}")
        print(f"   Repo: {b['repo']}")
        if b.get('bounty_amount'):
            print(f"   💰 ${b['bounty_amount']}")
    
    print("\n" + "=" * 70)
    print("\nTo create PRs manually:")
    print()
    print("1. Visit the issue URL in your browser")
    print("2. Click 'Fork' to fork the repository to your account")
    print("3. Clone your fork locally")
    print("4. Make the fix (typo, docs, formatting)")
    print("5. Push and create PR")
    print()
    print("Or, I can prepare the fixes and give you the commands to run:")
    print()
    
    # Show ready-to-fix repos
    repos_dir = '/agent/systems/bounty-hunter/data/repos'
    if os.path.exists(repos_dir):
        repos = os.listdir(repos_dir)
        if repos:
            print("📁 Repos already cloned with fixes applied:")
            for repo in repos[:5]:
                repo_path = os.path.join(repos_dir, repo)
                print(f"   - {repo}")
                
                # Check git status
                try:
                    result = subprocess.run(
                        ['git', 'status', '--short'],
                        cwd=repo_path,
                        capture_output=True,
                        text=True
                    )
                    if result.stdout.strip():
                        changes = len(result.stdout.strip().split('\n'))
                        print(f"     ({changes} files modified)")
                        
                        # Show the commands needed
                        print(f"\n     Commands to create PR:")
                        print(f"     cd {repo_path}")
                        print(f"     git remote add myfork https://github.com/{USERNAME}/{repo.split('_')[-1]}.git")
                        print(f"     git checkout -b fix-autonomy")
                        print(f"     git add .")
                        print(f"     git commit -m 'Fix: Automated typo and formatting fixes'")
                        print(f"     git push myfork fix-autonomy")
                        print(f"     # Then create PR on GitHub")
                        print()
                except:
                    pass

if __name__ == "__main__":
    main()
