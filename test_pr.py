#!/usr/bin/env python3
"""
Bounty Hunter PR Fixer - Debug and fix PR creation issues
"""

import os
import subprocess
import requests
import time

GITHUB_TOKEN = open('/secrets/github_token').read().strip()
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}

def test_fork_and_push():
    """Test the fork and push workflow"""
    
    # Test repo
    owner = 'OtowoOrg'
    repo = 'Stellar-K8s'
    
    work_dir = f'/agent/systems/bounty-hunter/data/repos/{owner}_{repo}'
    
    print(f"Testing fork and push for {owner}/{repo}")
    print("=" * 60)
    
    # Step 1: Fork
    print("\n1. Creating fork...")
    fork_url = f'https://api.github.com/repos/{owner}/{repo}/forks'
    response = requests.post(fork_url, headers=HEADERS)
    
    if response.status_code in [202, 201]:
        fork_data = response.json()
        print(f"   ✅ Fork created: {fork_data['full_name']}")
        print(f"   URL: {fork_data['html_url']}")
        fork_owner = fork_data['owner']['login']
    else:
        print(f"   ⚠️  Fork returned {response.status_code} - may already exist")
        fork_owner = 'kambrosgroup'
    
    # Step 2: Wait for fork
    print("\n2. Waiting for fork to be ready...")
    time.sleep(5)
    
    # Step 3: Check if repo exists locally
    print("\n3. Checking local repo...")
    if os.path.exists(work_dir):
        print(f"   📁 Repo exists at {work_dir}")
        
        # Configure git
        subprocess.run(['git', 'config', 'user.email', 'karlambrosius@outlook.com.au'],
                      cwd=work_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Karl Ambrosius'],
                      cwd=work_dir, check=True, capture_output=True)
        
        # Check current remotes
        result = subprocess.run(['git', 'remote', '-v'], cwd=work_dir, capture_output=True, text=True)
        print(f"   Current remotes:\n{result.stdout}")
        
        # Add fork remote
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{fork_owner}/{repo}.git"
        
        # Remove existing fork remote if any
        subprocess.run(['git', 'remote', 'remove', 'fork'], cwd=work_dir, capture_output=True)
        
        # Add new fork remote
        result = subprocess.run(['git', 'remote', 'add', 'fork', remote_url],
                               cwd=work_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ⚠️  Add remote failed: {result.stderr}")
        else:
            print(f"   ✅ Fork remote added")
        
        # Create test branch
        branch_name = "test-autonomy-fix"
        subprocess.run(['git', 'checkout', '-b', branch_name], cwd=work_dir, capture_output=True)
        print(f"   ✅ Branch created: {branch_name}")
        
        # Make a small change
        test_file = f"{work_dir}/AUTONOMY_TEST.md"
        with open(test_file, 'w') as f:
            f.write("# Test file\n\nThis is a test from Karl Ambrosius\n")
        
        subprocess.run(['git', 'add', 'AUTONOMY_TEST.md'], cwd=work_dir, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Test commit from Karl Ambrosius'], cwd=work_dir, capture_output=True)
        print(f"   ✅ Test commit created")
        
        # Try to push
        print("\n4. Pushing to fork...")
        result = subprocess.run(['git', 'push', '-f', 'fork', branch_name],
                               cwd=work_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Push successful!")
            print(f"   Output: {result.stdout}")
        else:
            print(f"   ❌ Push failed: {result.returncode}")
            print(f"   stderr: {result.stderr}")
            print(f"   stdout: {result.stdout}")
    else:
        print(f"   ❌ Repo not found at {work_dir}")

if __name__ == "__main__":
    test_fork_and_push()
