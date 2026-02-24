#!/usr/bin/env python3
"""
Security Bounty Hunter - AUTONOMY-CLAW
Finds and fixes security vulnerabilities for bug bounties
"""

import os
import json
import re
import subprocess
import requests
from datetime import datetime
from typing import List, Dict, Optional

class SecurityBountyHunter:
    """Hunts for security-related bounties and automated fixes"""
    
    def __init__(self):
        self.data_dir = "/agent/systems/bounty-hunter/security"
        os.makedirs(self.data_dir, exist_ok=True)
        self.github_token = open('/secrets/github_token').read().strip()
        self.headers = {'Authorization': f'token {self.github_token}', 'Accept': 'application/vnd.github.v3+json'}
        self.username = 'kambrosgroup'
        
    def search_security_bounties(self) -> List[Dict]:
        """Search for security-related issues and bounties"""
        bounties = []
        
        # GitHub Security Advisory searches
        queries = [
            'is:issue is:open label:security "vulnerability"',
            'is:issue is:open label:CVE',
            'is:issue is:open label:security "dependabot"',
            'is:issue is:open "security" "bounty"',
            'is:issue is:open label:bug-bounty',
        ]
        
        for query in queries:
            try:
                url = 'https://api.github.com/search/issues'
                params = {'q': query, 'sort': 'updated', 'order': 'desc', 'per_page': 20}
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    for item in response.json().get('items', []):
                        bounty = self._parse_security_issue(item)
                        if bounty:
                            bounties.append(bounty)
            except Exception as e:
                print(f"   Error: {e}")
        
        return bounties
    
    def _parse_security_issue(self, issue: Dict) -> Optional[Dict]:
        """Parse security issue"""
        title = issue.get('title', '').lower()
        body = issue.get('body', '') or ''
        labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
        
        # Check for security patterns
        security_patterns = ['cve', 'vulnerability', 'security', 'xss', 'sql injection', 
                            'rce', 'buffer overflow', 'dependabot', 'npm audit']
        
        is_security = any(p in title or p in body.lower() for p in security_patterns)
        is_security = is_security or any('security' in l or 'cve' in l for l in labels)
        
        if not is_security:
            return None
        
        # Extract bounty amount
        bounty_patterns = [r'\$([\d,]+)', r'bounty[:\s]+\$?([\d,]+)']
        amounts = []
        for pattern in bounty_patterns:
            matches = re.findall(pattern, title + ' ' + body, re.IGNORECASE)
            for match in matches:
                try:
                    amounts.append(float(match.replace(',', '')))
                except:
                    pass
        
        # Score based on severity and bounty
        score = 0
        if amounts:
            score += min(max(amounts) / 100, 100)
        if 'critical' in title or 'critical' in labels:
            score += 50
        if 'high' in title or 'high' in labels:
            score += 30
        
        return {
            'id': issue.get('id'),
            'title': issue.get('title'),
            'url': issue.get('html_url'),
            'repo': issue.get('repository_url', '').split('/')[-1] if issue.get('repository_url') else 'unknown',
            'bounty_amount': max(amounts) if amounts else None,
            'labels': labels,
            'is_security': True,
            'score': score,
            'platform': 'github'
        }
    
    def check_dependency_vulnerabilities(self, work_dir: str) -> List[Dict]:
        """Check for dependency vulnerabilities"""
        vulnerabilities = []
        
        # Check package.json for npm audit issues
        if os.path.exists(f"{work_dir}/package.json"):
            try:
                result = subprocess.run(['npm', 'audit', '--json'], 
                                      cwd=work_dir, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    for vuln in audit_data.get('vulnerabilities', {}).values():
                        vulnerabilities.append({
                            'package': vuln.get('name'),
                            'severity': vuln.get('severity'),
                            'fixAvailable': vuln.get('fixAvailable', False)
                        })
            except:
                pass
        
        # Check requirements.txt for Python vulnerabilities
        if os.path.exists(f"{work_dir}/requirements.txt"):
            try:
                result = subprocess.run(['pip-audit', '--format=json'], 
                                      cwd=work_dir, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    audit_data = json.loads(result.stdout)
                    for vuln in audit_data.get('dependencies', []):
                        for v in vuln.get('vulns', []):
                            vulnerabilities.append({
                                'package': vuln.get('name'),
                                'severity': v.get('severity'),
                                'fixAvailable': True
                            })
            except:
                pass
        
        return vulnerabilities
    
    def fix_dependencies(self, work_dir: str) -> Dict:
        """Attempt to fix dependency vulnerabilities"""
        results = {'fixed': [], 'failed': []}
        
        # Try npm audit fix
        if os.path.exists(f"{work_dir}/package.json"):
            try:
                subprocess.run(['npm', 'audit', 'fix', '--force'], 
                             cwd=work_dir, capture_output=True, timeout=120)
                results['fixed'].append('npm audit fix')
            except:
                results['failed'].append('npm audit fix')
        
        return results
    
    def run(self):
        """Main execution"""
        print(f"🔒 Security Bounty Hunter starting at {datetime.now()}")
        print("=" * 70)
        
        bounties = self.search_security_bounties()
        print(f"\n🔍 Found {len(bounties)} security bounties")
        
        # Sort by score
        bounties.sort(key=lambda x: x['score'], reverse=True)
        
        print("\nTop Security Opportunities:")
        print("-" * 70)
        
        for i, b in enumerate(bounties[:10], 1):
            print(f"\n{i}. {b['title'][:60]}")
            print(f"   Repo: {b['repo']} | Score: {b['score']:.1f}")
            if b.get('bounty_amount'):
                print(f"   💰 ${b['bounty_amount']}")
        
        # Save results
        results_file = f"{self.data_dir}/security_bounties_{datetime.now().strftime('%Y%m%d')}.json"
        with open(results_file, 'w') as f:
            json.dump(bounties, f, indent=2)
        
        print(f"\n💾 Results saved: {results_file}")
        return bounties

if __name__ == "__main__":
    hunter = SecurityBountyHunter()
    hunter.run()
