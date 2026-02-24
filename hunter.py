#!/usr/bin/env python3
"""
GitHub Bounty Hunter - Karl Ambrosius System 4
Automates finding, fixing, and submitting GitHub issues with bounties
"""

import os
import json
import re
import subprocess
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import requests

class BountyHunter:
    def __init__(self):
        self.data_dir = "/agent/systems/bounty-hunter/data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.state_file = f"{self.data_dir}/state.json"
        self.state = self.load_state()
        
        # GitHub config
        self.github_token = os.getenv('GITHUB_TOKEN') or self._read_secret('github_token')
        self.github_username = os.getenv('GITHUB_USERNAME') or 'autonomy-claw'
        
        # Headers for GitHub API
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        } if self.github_token else {}
        
    def _read_secret(self, name: str) -> Optional[str]:
        path = f'/secrets/{name}'
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read().strip()
        return None
    
    def load_state(self) -> Dict:
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'bounties_found': [],
            'bounties_attempted': [],
            'bounties_completed': [],
            'total_earned': 0,
            'repos_analyzed': []
        }
    
    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def search_bounty_issues(self) -> List[Dict]:
        """Search GitHub for issues with bounties"""
        bounties = []
        
        # Search queries for different bounty platforms
        queries = [
            'label:bounty state:open',
            'label:"good first issue" label:bounty state:open',
            '"$" in:title state:open label:bug',
            'label:"bug bounty" state:open',
            'label:"help wanted" "bounty" state:open',
            'label:reward state:open',
            '"bounty" "reward" state:open',
        ]
        
        for query in queries:
            try:
                url = f'https://api.github.com/search/issues'
                params = {
                    'q': query,
                    'sort': 'updated',
                    'order': 'desc',
                    'per_page': 30
                }
                
                if self.github_token:
                    response = requests.get(url, headers=self.headers, params=params, timeout=30)
                else:
                    response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        bounty = self._parse_bounty(item)
                        if bounty and bounty not in bounties:
                            bounties.append(bounty)
                            
            except Exception as e:
                print(f"Error searching '{query}': {e}")
        
        return bounties
    
    def _parse_bounty(self, issue: Dict) -> Optional[Dict]:
        """Parse issue to extract bounty details"""
        title = issue.get('title', '')
        body = issue.get('body', '') or ''
        
        # Look for bounty amounts in title/body
        bounty_patterns = [
            r'\$([\d,]+(?:\.\d{2})?)',  # $100, $1,000.00
            r'(\d+(?:\.\d{2})?)\s*USD',  # 100 USD
            r'bounty[:\s]+\$?([\d,]+)',  # bounty: $100
            r'reward[:\s]+\$?([\d,]+)',  # reward: 100
        ]
        
        amounts = []
        for pattern in bounty_patterns:
            matches = re.findall(pattern, title + ' ' + body, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if 10 <= amount <= 10000:  # Reasonable bounty range
                        amounts.append(amount)
                except:
                    pass
        
        # Also check for "good first issue" labels (learning opportunity)
        labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
        is_good_first = any('good first issue' in l or 'beginner' in l for l in labels)
        
        if not amounts and not is_good_first:
            return None
        
        return {
            'id': issue.get('id'),
            'number': issue.get('number'),
            'title': title,
            'url': issue.get('html_url'),
            'repo': issue.get('repository_url', '').split('/')[-1] if issue.get('repository_url') else 'unknown',
            'body': body[:500] + '...' if len(body) > 500 else body,
            'bounty_amount': max(amounts) if amounts else None,
            'labels': labels,
            'is_good_first': is_good_first,
            'created_at': issue.get('created_at'),
            'updated_at': issue.get('updated_at'),
            'state': issue.get('state'),
            'score': self._calculate_score(issue, amounts, is_good_first)
        }
    
    def _calculate_score(self, issue: Dict, amounts: List[float], is_good_first: bool) -> float:
        """Calculate priority score for bounty"""
        score = 0
        
        # Bounty amount (higher = better)
        if amounts:
            score += min(max(amounts) / 100, 50)  # Cap at 50 points
        
        # Good first issue bonus
        if is_good_first:
            score += 20
        
        # Recent activity bonus
        updated = issue.get('updated_at', '')
        if updated:
            try:
                from datetime import datetime
                updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                days_old = (datetime.now(updated_dt.tzinfo) - updated_dt).days
                if days_old < 7:
                    score += 10
                elif days_old < 30:
                    score += 5
            except:
                pass
        
        return score
    
    def analyze_issue_fixability(self, bounty: Dict) -> Dict:
        """Analyze if issue can be automatically fixed"""
        analysis = {
            'can_fix': False,
            'fix_type': None,
            'confidence': 0,
            'approach': None
        }
        
        title_lower = bounty['title'].lower()
        body_lower = bounty['body'].lower()
        combined = title_lower + ' ' + body_lower
        
        # Pattern matching for fixable issues
        
        # 1. Typo fixes
        typo_patterns = ['typo', 'spelling', 'misspelled', 'fix typo', 'correct spelling']
        if any(p in combined for p in typo_patterns):
            analysis['can_fix'] = True
            analysis['fix_type'] = 'typo'
            analysis['confidence'] = 0.8
            analysis['approach'] = 'Find and replace typo in codebase'
        
        # 2. Documentation fixes
        doc_patterns = ['readme', 'documentation', 'docs', 'update doc', 'fix link']
        if any(p in combined for p in doc_patterns):
            analysis['can_fix'] = True
            analysis['fix_type'] = 'documentation'
            analysis['confidence'] = 0.7
            analysis['approach'] = 'Update documentation files'
        
        # 3. Simple dependency updates
        dep_patterns = ['update dependency', 'bump version', 'security patch', 'cve']
        if any(p in combined for p in dep_patterns):
            analysis['can_fix'] = True
            analysis['fix_type'] = 'dependency'
            analysis['confidence'] = 0.6
            analysis['approach'] = 'Update package.json/requirements.txt'
        
        # 4. Broken link fixes
        link_patterns = ['broken link', '404', 'dead link', 'link rot']
        if any(p in combined for p in link_patterns):
            analysis['can_fix'] = True
            analysis['fix_type'] = 'link_fix'
            analysis['confidence'] = 0.5
            analysis['approach'] = 'Find and update broken URLs'
        
        # 5. Code style/linting
        lint_patterns = ['lint', 'format', 'code style', 'prettier', 'eslint']
        if any(p in combined for p in lint_patterns):
            analysis['can_fix'] = True
            analysis['fix_type'] = 'linting'
            analysis['confidence'] = 0.9
            analysis['approach'] = 'Run linter/formatter'
        
        return analysis
    
    def clone_and_analyze(self, bounty: Dict) -> Optional[str]:
        """Clone repository and analyze the issue"""
        repo_name = bounty['repo']
        repo_url = f"https://github.com/{bounty['url'].split('/')[3]}/{repo_name}"
        
        work_dir = f"/agent/systems/bounty-hunter/repos/{repo_name}"
        os.makedirs(os.path.dirname(work_dir), exist_ok=True)
        
        # Clone if not exists
        if not os.path.exists(work_dir):
            try:
                subprocess.run(['git', 'clone', repo_url, work_dir], 
                             check=True, capture_output=True, timeout=60)
                print(f"✅ Cloned {repo_name}")
            except Exception as e:
                print(f"❌ Failed to clone {repo_name}: {e}")
                return None
        
        return work_dir
    
    def attempt_fix(self, bounty: Dict, work_dir: str) -> Optional[Dict]:
        """Attempt to fix the issue"""
        analysis = self.analyze_issue_fixability(bounty)
        
        if not analysis['can_fix']:
            return None
        
        fix_result = {
            'bounty': bounty,
            'analysis': analysis,
            'success': False,
            'changes': [],
            'pr_url': None
        }
        
        fix_type = analysis['fix_type']
        
        try:
            if fix_type == 'linting':
                fix_result = self._fix_linting(bounty, work_dir, fix_result)
            elif fix_type == 'typo':
                fix_result = self._fix_typo(bounty, work_dir, fix_result)
            elif fix_type == 'documentation':
                fix_result = self._fix_documentation(bounty, work_dir, fix_result)
            elif fix_type == 'dependency':
                fix_result = self._fix_dependency(bounty, work_dir, fix_result)
            
        except Exception as e:
            print(f"❌ Fix failed: {e}")
            fix_result['error'] = str(e)
        
        return fix_result
    
    def _fix_linting(self, bounty: Dict, work_dir: str, result: Dict) -> Dict:
        """Fix linting and code style issues"""
        from smart_fixer import SmartFixer
        
        print("   🤖 Running smart fixes...")
        fix_results = SmartFixer.run_all_fixes(work_dir)
        
        result['changes'].append(f"Fixed {fix_results['typos_fixed']} typos")
        result['changes'].append(f"Fixed {fix_results['trailing_ws_fixed']} files with trailing whitespace")
        result['changes'].append(f"Added newlines to {fix_results['newlines_added']} files")
        
        # Also try language-specific linters
        if os.path.exists(f"{work_dir}/package.json"):
            for cmd in [['npx', 'eslint', '--fix', '.'], ['npx', 'prettier', '--write', '.']]:
                try:
                    subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True, timeout=120)
                    result['changes'].append(f"Ran {' '.join(cmd)}")
                except:
                    pass
        
        if os.path.exists(f"{work_dir}/setup.py") or os.path.glob(f"{work_dir}/*.py"):
            for cmd in [['black', '.'], ['autopep8', '--in-place', '--recursive', '.']]:
                try:
                    subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True, timeout=120)
                    result['changes'].append(f"Ran {' '.join(cmd)}")
                except:
                    pass
        
        result['success'] = fix_results['total_changes'] > 0 or len(result['changes']) > 0
        result['fix_details'] = fix_results
        return result
    
    def _fix_typo(self, bounty: Dict, work_dir: str, result: Dict) -> Dict:
        """Attempt to fix typos"""
        # Extract potential typo from issue
        body = bounty.get('body', '')
        
        # Look for "X should be Y" patterns
        patterns = [
            r'"([^"]+)"\s+should\s+be\s+"([^"]+)"',
            r'\b([a-zA-Z]+)\b\s+->\s+\b([a-zA-Z]+)\b',
            r'replace\s+["\']?([^"\']+)["\']?\s+with\s+["\']?([^"\']+)["\']?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for wrong, correct in matches:
                # Search and replace in files
                try:
                    result = self._search_replace_files(work_dir, wrong, correct, result)
                except Exception as e:
                    print(f"Replace failed: {e}")
        
        result['success'] = len(result['changes']) > 0
        return result
    
    def _search_replace_files(self, work_dir: str, old: str, new: str, result: Dict) -> Dict:
        """Search and replace text in files"""
        import fnmatch
        
        for root, dirs, files in os.walk(work_dir):
            # Skip hidden dirs and common non-source dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
            
            for filename in files:
                if any(filename.endswith(ext) for ext in ['.md', '.txt', '.py', '.js', '.ts', '.json', '.yml', '.yaml']):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if old in content:
                            new_content = content.replace(old, new)
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            rel_path = os.path.relpath(filepath, work_dir)
                            result['changes'].append(f"Fixed typo in {rel_path}: '{old}' -> '{new}'")
                    except:
                        pass
        
        return result
    
    def _fix_documentation(self, bounty: Dict, work_dir: str, result: Dict) -> Dict:
        """Fix documentation issues"""
        # Similar to typo fix but focused on docs
        result = self._fix_typo(bounty, work_dir, result)
        result['success'] = len(result['changes']) > 0
        return result
    
    def _fix_dependency(self, bounty: Dict, work_dir: str, result: Dict) -> Dict:
        """Fix dependency issues"""
        # Parse CVE or version requirement from issue
        body = bounty.get('body', '')
        
        # Look for package names and versions
        # This is simplified - real implementation would be more sophisticated
        
        result['success'] = False
        result['note'] = 'Dependency fixes require manual review for security'
        return result
    
    def create_pull_request(self, bounty: Dict, fix_result: Dict, work_dir: str) -> Optional[Dict]:
        """Create a pull request with the fix using GitHub API"""
        if not fix_result['success'] or not self.github_token:
            return None
        
        try:
            # Get repo details from issue URL
            issue_url = bounty['url']
            parts = issue_url.split('/')
            owner = parts[3]
            repo = parts[4]
            issue_number = parts[6]
            
            print(f"   📤 Creating PR for {owner}/{repo}#{issue_number}")
            
            # Configure git
            subprocess.run(['git', 'config', 'user.email', 'karlambrosius@outlook.com.au'], 
                          cwd=work_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Karl Ambrosius'], 
                          cwd=work_dir, check=True, capture_output=True)
            
            # Fork the repository first (if needed)
            fork_result = self._ensure_fork(owner, repo)
            if not fork_result:
                print("   ⚠️  Could not fork/verify fork, trying direct PR")
                fork_owner = owner  # Assume we have write access
            else:
                fork_owner = fork_result
            
            # Create branch
            branch_name = f"autonomy-fix-{issue_number}"
            subprocess.run(['git', 'checkout', '-b', branch_name], 
                          cwd=work_dir, check=True, capture_output=True)
            
            # Commit changes
            subprocess.run(['git', 'add', '-A'], cwd=work_dir, check=True, capture_output=True)
            
            # Build commit message
            changes_summary = '\n'.join([f"- {c}" for c in fix_result['changes'][:5]])
            commit_msg = f"Fix #{issue_number}: {bounty['title'][:50]}\n\n{changes_summary}\n\nAutomated fix by Karl Ambrosius 🤖"
            
            subprocess.run(['git', 'commit', '-m', commit_msg], 
                          cwd=work_dir, check=True, capture_output=True)
            
            # Push to fork
            remote_url = f"https://{self.github_token}@github.com/{fork_owner}/{repo}.git"
            subprocess.run(['git', 'remote', 'add', 'fork', remote_url], 
                          cwd=work_dir, capture_output=True)
            
            push_result = subprocess.run(
                ['git', 'push', '-u', 'fork', branch_name],
                cwd=work_dir, capture_output=True, text=True
            )
            
            if push_result.returncode != 0:
                # Try force push if branch exists
                push_result = subprocess.run(
                    ['git', 'push', '-f', '-u', 'fork', branch_name],
                    cwd=work_dir, capture_output=True, text=True
                )
            
            if push_result.returncode != 0:
                print(f"   ❌ Push failed: {push_result.stderr}")
                return None
            
            # Create PR via GitHub API
            pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            pr_data = {
                "title": f"Fix #{issue_number}: {bounty['title'][:60]}",
                "body": f"## Automated Fix\n\nThis PR addresses issue #{issue_number}.\n\n### Changes Made:\n{changes_summary}\n\n### Testing:\n- [ ] Automated tests pass\n- [ ] Changes reviewed\n\n---\n*Generated by Karl Ambrosius* 🤖",
                "head": f"{fork_owner}:{branch_name}",
                "base": "main"  # or "master", detect dynamically
            }
            
            response = requests.post(pr_url, headers=self.headers, json=pr_data, timeout=30)
            
            if response.status_code == 201:
                pr_info = response.json()
                print(f"   ✅ PR created: {pr_info['html_url']}")
                return {
                    'pr_url': pr_info['html_url'],
                    'pr_number': pr_info['number'],
                    'branch': branch_name
                }
            else:
                print(f"   ❌ PR creation failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"   ❌ PR creation error: {e}")
            return None
    
    def _ensure_fork(self, owner: str, repo: str) -> Optional[str]:
        """Ensure repository is forked, return fork owner"""
        try:
            # Check if already forked
            forks_url = f"https://api.github.com/repos/{owner}/{repo}/forks"
            response = requests.get(forks_url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                forks = response.json()
                for fork in forks:
                    if fork['owner']['login'] == self.github_username:
                        print(f"   📋 Found existing fork")
                        return self.github_username
            
            # Create fork
            print(f"   🍴 Creating fork...")
            fork_url = f"https://api.github.com/repos/{owner}/{repo}/forks"
            response = requests.post(fork_url, headers=self.headers, timeout=30)
            
            if response.status_code in [202, 201]:
                print(f"   ✅ Fork created")
                return self.github_username
            else:
                print(f"   ⚠️  Fork creation returned {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ⚠️  Fork check/creation failed: {e}")
            return None
    
    def run(self):
        """Main execution loop"""
        print(f"🎯 Bounty Hunter starting at {datetime.now()}")
        
        if not self.github_token:
            print("⚠️  No GitHub token found. Set GITHUB_TOKEN env var or /secrets/github_token")
            print("   Limited to public API (60 requests/hour)")
        
        # Search for bounties
        print("🔍 Searching for bounty issues...")
        bounties = self.search_bounty_issues()
        print(f"✅ Found {len(bounties)} potential bounties")
        
        # Sort by score
        bounties.sort(key=lambda x: x['score'], reverse=True)
        
        # Analyze top bounties
        print("\n📊 Top Bounties:")
        print("=" * 80)
        
        attempted = 0
        for i, bounty in enumerate(bounties[:10], 1):
            print(f"\n{i}. {bounty['title'][:60]}")
            print(f"   Repo: {bounty['repo']} | Score: {bounty['score']:.1f}")
            if bounty['bounty_amount']:
                print(f"   💰 Bounty: ${bounty['bounty_amount']}")
            
            # Analyze fixability
            analysis = self.analyze_issue_fixability(bounty)
            print(f"   🔧 Can Fix: {analysis['can_fix']} | Type: {analysis['fix_type']} | Confidence: {analysis['confidence']}")
            
            if analysis['can_fix'] and analysis['confidence'] >= 0.6 and attempted < 3:
                print(f"   🚀 Attempting fix...")
                work_dir = self.clone_and_analyze(bounty)
                if work_dir:
                    fix_result = self.attempt_fix(bounty, work_dir)
                    if fix_result and fix_result['success']:
                        branch = self.create_pull_request(bounty, fix_result, work_dir)
                        if branch:
                            self.state['bounties_attempted'].append({
                                'issue_url': bounty['url'],
                                'branch': branch,
                                'changes': fix_result['changes'],
                                'timestamp': datetime.now().isoformat()
                            })
                            attempted += 1
                print(f"   ✅ Fix attempted")
        
        # Update state
        self.state['bounties_found'] = bounties
        self.save_state()
        
        print(f"\n🎯 Bounty Hunter complete.")
        print(f"   Found: {len(bounties)} bounties")
        print(f"   Attempted: {attempted} fixes")
        print(f"   State saved to: {self.state_file}")

if __name__ == "__main__":
    hunter = BountyHunter()
    hunter.run()
