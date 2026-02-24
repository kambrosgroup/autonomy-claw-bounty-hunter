#!/usr/bin/env python3
"""
Dependency Update Bounty Hunter - Karl Ambrosius
Finds outdated dependencies and creates PRs to update them
"""

import os
import json
import subprocess
import requests
from datetime import datetime
from typing import List, Dict, Optional

class DependencyBountyHunter:
    """Hunts for dependency update opportunities"""
    
    def __init__(self):
        self.data_dir = "/agent/systems/bounty-hunter/dependency"
        os.makedirs(self.data_dir, exist_ok=True)
        self.github_token = open('/secrets/github_token').read().strip()
        self.headers = {'Authorization': f'token {self.github_token}', 'Accept': 'application/vnd.github.v3+json'}
        self.username = 'KarlAmbrosius'
        
    def search_dependency_issues(self) -> List[Dict]:
        """Search for dependency update issues"""
        issues = []
        
        queries = [
            'is:issue is:open "update dependency"',
            'is:issue is:open "bump version"',
            'is:issue is:open "upgrade to" label:dependencies',
            'is:issue is:open label:dependencies',
            'is:issue is:open "outdated dependencies"',
        ]
        
        for query in queries:
            try:
                url = 'https://api.github.com/search/issues'
                params = {'q': query, 'sort': 'updated', 'order': 'desc', 'per_page': 20}
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    for item in response.json().get('items', []):
                        issue = self._parse_dependency_issue(item)
                        if issue:
                            issues.append(issue)
            except Exception as e:
                print(f"   Error: {e}")
        
        return issues
    
    def _parse_dependency_issue(self, issue: Dict) -> Optional[Dict]:
        """Parse dependency issue"""
        title = issue.get('title', '').lower()
        labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
        
        # Check for dependency patterns
        dep_patterns = ['update', 'bump', 'upgrade', 'dependencies', 'package', 'version']
        is_dep = any(p in title for p in dep_patterns) or 'dependencies' in labels
        
        if not is_dep:
            return None
        
        return {
            'id': issue.get('id'),
            'title': issue.get('title'),
            'url': issue.get('html_url'),
            'repo': issue.get('repository_url', '').split('/')[-1] if issue.get('repository_url') else 'unknown',
            'labels': labels,
            'score': 20 if 'dependencies' in labels else 10
        }
    
    def update_dependencies(self, work_dir: str) -> Dict:
        """Update dependencies in a repository"""
        results = {'updated': [], 'failed': []}
        
        # Node.js projects
        if os.path.exists(f"{work_dir}/package.json"):
            try:
                # Check for outdated packages
                result = subprocess.run(['npm', 'outdated', '--json'], 
                                      cwd=work_dir, capture_output=True, text=True, timeout=60)
                if result.stdout:
                    outdated = json.loads(result.stdout)
                    if outdated:
                        # Update all packages
                        subprocess.run(['npm', 'update'], cwd=work_dir, capture_output=True, timeout=120)
                        results['updated'].append(f"npm packages: {len(outdated)}")
            except:
                pass
        
        # Python projects
        if os.path.exists(f"{work_dir}/requirements.txt"):
            try:
                # Use pip-compile if available
                if os.path.exists(f"{work_dir}/requirements.in"):
                    subprocess.run(['pip-compile', '--upgrade'], cwd=work_dir, capture_output=True, timeout=120)
                    results['updated'].append('pip requirements')
            except:
                pass
        
        # Rust projects
        if os.path.exists(f"{work_dir}/Cargo.toml"):
            try:
                subprocess.run(['cargo', 'update'], cwd=work_dir, capture_output=True, timeout=120)
                results['updated'].append('cargo dependencies')
            except:
                pass
        
        return results
    
    def run(self):
        """Main execution"""
        print(f"📦 Dependency Bounty Hunter starting at {datetime.now()}")
        print("=" * 70)
        
        issues = self.search_dependency_issues()
        print(f"\n🔍 Found {len(issues)} dependency update opportunities")
        
        issues.sort(key=lambda x: x['score'], reverse=True)
        
        print("\nTop Opportunities:")
        print("-" * 70)
        
        for i, issue in enumerate(issues[:10], 1):
            print(f"\n{i}. {issue['title'][:60]}")
            print(f"   Repo: {issue['repo']}")
        
        # Save results
        results_file = f"{self.data_dir}/dependency_issues_{datetime.now().strftime('%Y%m%d')}.json"
        with open(results_file, 'w') as f:
            json.dump(issues, f, indent=2)
        
        print(f"\n💾 Results saved: {results_file}")
        return issues

if __name__ == "__main__":
    hunter = DependencyBountyHunter()
    hunter.run()
