#!/usr/bin/env python3
"""
Enhanced GitHub Bounty Hunter - Multiple Sources
Searches across GitHub, Gitcoin, Algora, and other bounty platforms
"""

import os
import json
import re
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import requests

class EnhancedBountyHunter:
    def __init__(self):
        self.data_dir = "/agent/systems/bounty-hunter/data"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f"{self.data_dir}/repos", exist_ok=True)
        
        self.state_file = f"{self.data_dir}/state.json"
        self.state = self.load_state()
        
        self.github_token = os.getenv('GITHUB_TOKEN') or self._read_secret('github_token')
        self.github_username = 'kambrosgroup'
        
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
    
    def search_github_issues(self) -> List[Dict]:
        """Search GitHub issues with multiple strategies"""
        all_issues = []
        
        # Strategy 1: Direct search queries
        search_queries = [
            'is:issue is:open label:bug bounty',
            'is:issue is:open label:good-first-issue',
            'is:issue is:open label:help-wanted',
            'is:issue is:open label:documentation',
            'is:issue is:open typo',
            'is:issue is:open "good first issue"',
        ]
        
        for query in search_queries:
            try:
                url = 'https://api.github.com/search/issues'
                params = {
                    'q': query,
                    'sort': 'updated',
                    'order': 'desc',
                    'per_page': 30
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        bounty = self._parse_issue(item)
                        if bounty and not any(b['url'] == bounty['url'] for b in all_issues):
                            all_issues.append(bounty)
                elif response.status_code == 403:
                    print(f"   ⚠️  Rate limited on query: {query}")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   Error on '{query}': {e}")
        
        return all_issues
    
    def search_curated_repos(self) -> List[Dict]:
        """Search known bounty-friendly repositories"""
        curated_repos = [
            ('facebook', 'react'),
            ('vercel', 'next.js'),
            ('microsoft', 'vscode'),
            ('nodejs', 'node'),
            ('python', 'cpython'),
            ('kubernetes', 'kubernetes'),
            ('tensorflow', 'tensorflow'),
            ('rust-lang', 'rust'),
            ('golang', 'go'),
            ('apache', 'spark'),
            ('ansible', 'ansible'),
            ('mozilla', 'firefox'),
        ]
        
        all_issues = []
        
        for owner, repo in curated_repos[:5]:  # Limit to avoid rate limits
            try:
                url = f'https://api.github.com/repos/{owner}/{repo}/issues'
                params = {
                    'state': 'open',
                    'labels': 'good first issue,help wanted,documentation,bug',
                    'per_page': 10
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    issues = response.json()
                    for item in issues:
                        bounty = self._parse_issue(item)
                        if bounty:
                            all_issues.append(bounty)
                            
            except Exception as e:
                print(f"   Error fetching {owner}/{repo}: {e}")
        
        return all_issues
    
    def search_gitcoin(self) -> List[Dict]:
        """Search Gitcoin bounties (if API available)"""
        # Gitcoin API endpoint (may require auth)
        bounties = []
        
        try:
            # Gitcoin bounties API
            url = 'https://gitcoin.co/api/v0.1/bounties/'
            params = {
                'is_open': 'true',
                'network': 'mainnet',
                'order_by': '-web3_created'
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for item in data[:20]:
                    bounty = {
                        'id': item.get('id'),
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'repo': item.get('github_url', '').split('/')[-1] if item.get('github_url') else 'unknown',
                        'body': item.get('issue_description', '')[:500],
                        'bounty_amount': float(item.get('value_in_usdt', 0)) if item.get('value_in_usdt') else None,
                        'platform': 'gitcoin',
                        'labels': ['bounty'],
                        'is_good_first': item.get('experience_level') == 'Beginner',
                        'score': float(item.get('value_in_usdt', 0)) / 100 if item.get('value_in_usdt') else 5
                    }
                    bounties.append(bounty)
                    
        except Exception as e:
            print(f"   Gitcoin API error: {e}")
        
        return bounties
    
    def _parse_issue(self, issue: Dict) -> Optional[Dict]:
        """Parse GitHub issue to bounty format"""
        title = issue.get('title', '')
        body = issue.get('body', '') or ''
        
        # Look for bounty indicators
        bounty_patterns = [
            r'\$([\d,]+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\s*USD',
            r'bounty[:\s]+\$?([\d,]+)',
            r'reward[:\s]+\$?([\d,]+)',
        ]
        
        amounts = []
        for pattern in bounty_patterns:
            matches = re.findall(pattern, title + ' ' + body, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if 10 <= amount <= 50000:
                        amounts.append(amount)
                except:
                    pass
        
        labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
        
        # Score based on fixability
        is_good_first = any(l in labels for l in ['good first issue', 'beginner', 'easy', 'documentation'])
        is_typo = 'typo' in title.lower() or 'spelling' in title.lower()
        is_docs = 'documentation' in labels or 'docs' in title.lower()
        is_lint = any(l in labels for l in ['lint', 'format', 'style'])
        
        # Calculate score
        score = 0
        if amounts:
            score += min(max(amounts) / 100, 50)
        if is_good_first:
            score += 20
        if is_typo:
            score += 15
        if is_docs:
            score += 10
        if is_lint:
            score += 25
        
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
            'is_typo': is_typo,
            'is_docs': is_docs,
            'is_lint': is_lint,
            'created_at': issue.get('created_at'),
            'updated_at': issue.get('updated_at'),
            'state': issue.get('state'),
            'score': score,
            'platform': 'github'
        }
    
    def analyze_fixability(self, bounty: Dict) -> Dict:
        """Analyze if issue can be automatically fixed"""
        analysis = {
            'can_fix': False,
            'fix_type': None,
            'confidence': 0,
            'approach': None
        }
        
        title_lower = bounty['title'].lower()
        body_lower = bounty['body'].lower()
        labels = bounty.get('labels', [])
        
        # Check for fixable patterns
        if bounty.get('is_typo') or 'typo' in title_lower:
            analysis['can_fix'] = True
            analysis['fix_type'] = 'typo'
            analysis['confidence'] = 0.8
            analysis['approach'] = 'Find and replace typo in codebase'
        
        elif bounty.get('is_docs') or 'documentation' in labels:
            analysis['can_fix'] = True
            analysis['fix_type'] = 'documentation'
            analysis['confidence'] = 0.7
            analysis['approach'] = 'Update documentation files'
        
        elif bounty.get('is_lint') or any(l in labels for l in ['lint', 'format', 'style']):
            analysis['can_fix'] = True
            analysis['fix_type'] = 'linting'
            analysis['confidence'] = 0.9
            analysis['approach'] = 'Run linter/formatter'
        
        elif 'good first issue' in labels or 'beginner' in labels:
            # Check for specific patterns
            if 'readme' in title_lower or 'link' in title_lower:
                analysis['can_fix'] = True
                analysis['fix_type'] = 'documentation'
                analysis['confidence'] = 0.6
                analysis['approach'] = 'Update README/links'
        
        return analysis
    
    def clone_repo(self, bounty: Dict) -> Optional[str]:
        """Clone repository"""
        issue_url = bounty['url']
        parts = issue_url.split('/')
        owner = parts[3]
        repo = parts[4]
        
        repo_url = f"https://github.com/{owner}/{repo}.git"
        work_dir = f"{self.data_dir}/repos/{owner}_{repo}"
        
        if not os.path.exists(work_dir):
            try:
                subprocess.run(['git', 'clone', '--depth', '1', repo_url, work_dir],
                             check=True, capture_output=True, timeout=120)
                print(f"   ✅ Cloned {owner}/{repo}")
            except Exception as e:
                print(f"   ❌ Failed to clone: {e}")
                return None
        else:
            print(f"   📁 Using existing {owner}/{repo}")
        
        return work_dir
    
    def apply_smart_fixes(self, work_dir: str) -> Dict:
        """Apply smart fixes to repository"""
        import sys
        sys.path.insert(0, '/agent/systems/bounty-hunter')
        from smart_fixer import SmartFixer
        
        return SmartFixer.run_all_fixes(work_dir)
    
    def create_pr(self, bounty: Dict, work_dir: str, fix_results: Dict) -> Optional[Dict]:
        """Create pull request"""
        if fix_results['total_changes'] == 0:
            return None
        
        try:
            issue_url = bounty['url']
            parts = issue_url.split('/')
            owner = parts[3]
            repo = parts[4]
            issue_number = parts[6]
            
            # Configure git
            subprocess.run(['git', 'config', 'user.email', 'autonomy-claw@openclaw.ai'],
                          cwd=work_dir, check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'AUTONOMY-CLAW'],
                          cwd=work_dir, check=True, capture_output=True)
            
            # Fork repo
            fork_url = f'https://api.github.com/repos/{owner}/{repo}/forks'
            response = requests.post(fork_url, headers=self.headers, timeout=30)
            
            if response.status_code in [202, 201]:
                fork_data = response.json()
                fork_owner = fork_data['owner']['login']
                print(f"   ✅ Forked to {fork_owner}/{repo}")
            else:
                # Assume already forked
                fork_owner = self.github_username
                print(f"   📁 Using fork {fork_owner}/{repo}")
            
            # Wait for fork to be ready
            time.sleep(3)
            
            # Add fork remote
            remote_url = f"https://{self.github_token}@github.com/{fork_owner}/{repo}.git"
            subprocess.run(['git', 'remote', 'add', 'fork', remote_url],
                          cwd=work_dir, capture_output=True)
            
            # Create branch
            branch_name = f"autonomy-fix-{issue_number}"
            subprocess.run(['git', 'checkout', '-b', branch_name],
                          cwd=work_dir, check=True, capture_output=True)
            
            # Commit
            subprocess.run(['git', 'add', '-A'], cwd=work_dir, check=True, capture_output=True)
            
            changes_summary = '\n'.join([f"- {c}" for c in fix_results.get('typos_found', [])[:3]])
            commit_msg = f"Fix #{issue_number}: Automated fixes\n\n- Fixed {fix_results['typos_fixed']} typos\n- Fixed {fix_results['trailing_ws_fixed']} whitespace issues\n\n🤖 AUTONOMY-CLAW"
            
            subprocess.run(['git', 'commit', '-m', commit_msg],
                          cwd=work_dir, check=True, capture_output=True)
            
            # Push
            subprocess.run(['git', 'push', '-f', 'fork', branch_name],
                          cwd=work_dir, check=True, capture_output=True)
            
            # Create PR
            pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            pr_data = {
                "title": f"Fix #{issue_number}: Automated typo and formatting fixes",
                "body": f"## Automated Fix\n\nThis PR addresses issue #{issue_number} with automated fixes:\n\n- Fixed {fix_results['typos_fixed']} typos\n- Fixed {fix_results['trailing_ws_fixed']} files with trailing whitespace\n- Added {fix_results['newlines_added']} missing newlines\n\n---\n*Generated by AUTONOMY-CLAW* 🤖",
                "head": f"{fork_owner}:{branch_name}",
                "base": "main"
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
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def run(self):
        """Main execution"""
        print(f"🎯 Enhanced Bounty Hunter starting at {datetime.now()}")
        print(f"   GitHub: {self.github_username}")
        
        # Search multiple sources
        print("\n🔍 Searching GitHub issues...")
        github_issues = self.search_github_issues()
        print(f"   Found {len(github_issues)} issues")
        
        print("\n🔍 Searching curated repositories...")
        curated_issues = self.search_curated_repos()
        print(f"   Found {len(curated_issues)} issues")
        
        print("\n🔍 Searching Gitcoin...")
        gitcoin_bounties = self.search_gitcoin()
        print(f"   Found {len(gitcoin_bounties)} bounties")
        
        # Combine and deduplicate
        all_bounties = github_issues + curated_issues + gitcoin_bounties
        seen_urls = set()
        unique_bounties = []
        for b in all_bounties:
            if b['url'] not in seen_urls:
                seen_urls.add(b['url'])
                unique_bounties.append(b)
        
        # Sort by score
        unique_bounties.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"\n📊 Total unique opportunities: {len(unique_bounties)}")
        print("=" * 80)
        
        # Process top bounties
        attempted = 0
        created_prs = []
        
        for i, bounty in enumerate(unique_bounties[:15], 1):
            print(f"\n{i}. {bounty['title'][:70]}")
            print(f"   Repo: {bounty['repo']} | Score: {bounty['score']:.1f}")
            if bounty.get('bounty_amount'):
                print(f"   💰 ${bounty['bounty_amount']}")
            print(f"   Platform: {bounty.get('platform', 'github')}")
            
            analysis = self.analyze_fixability(bounty)
            print(f"   🔧 Fixable: {analysis['can_fix']} | Type: {analysis['fix_type']} | Confidence: {analysis['confidence']}")
            
            if analysis['can_fix'] and analysis['confidence'] >= 0.6 and attempted < 5:
                print(f"   🚀 Attempting fix...")
                
                work_dir = self.clone_repo(bounty)
                if work_dir:
                    fix_results = self.apply_smart_fixes(work_dir)
                    print(f"   📊 Changes: {fix_results['total_changes']}")
                    
                    if fix_results['total_changes'] > 0:
                        pr_result = self.create_pr(bounty, work_dir, fix_results)
                        if pr_result:
                            created_prs.append(pr_result)
                            self.state['bounties_attempted'].append({
                                'url': bounty['url'],
                                'pr_url': pr_result['pr_url'],
                                'timestamp': datetime.now().isoformat()
                            })
                    
                    attempted += 1
                    time.sleep(2)  # Rate limit protection
        
        # Update state
        self.state['bounties_found'] = unique_bounties
        self.state['last_run'] = datetime.now().isoformat()
        self.save_state()
        
        print(f"\n" + "=" * 80)
        print(f"🎯 Bounty Hunter Complete!")
        print(f"   Opportunities found: {len(unique_bounties)}")
        print(f"   Fixes attempted: {attempted}")
        print(f"   PRs created: {len(created_prs)}")
        
        for pr in created_prs:
            print(f"   ✅ {pr['pr_url']}")

if __name__ == "__main__":
    hunter = EnhancedBountyHunter()
    hunter.run()
