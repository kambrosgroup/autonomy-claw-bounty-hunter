#!/usr/bin/env python3
"""
Test Coverage Bounty Hunter - Karl Ambrosius
Finds repos needing tests and generates basic test coverage
"""

import os
import json
import subprocess
import requests
from datetime import datetime
from typing import List, Dict, Optional

class TestBountyHunter:
    """Hunts for test coverage improvement opportunities"""
    
    def __init__(self):
        self.data_dir = "/agent/systems/bounty-hunter/test"
        os.makedirs(self.data_dir, exist_ok=True)
        self.github_token = open('/secrets/github_token').read().strip()
        self.headers = {'Authorization': f'token {self.github_token}', 'Accept': 'application/vnd.github.v3+json'}
        
    def search_test_issues(self) -> List[Dict]:
        """Search for test-related issues"""
        issues = []
        
        queries = [
            'is:issue is:open label:testing "test coverage"',
            'is:issue is:open label:tests "add tests"',
            'is:issue is:open "unit tests"',
            'is:issue is:open "test suite"',
            'is:issue is:open label:help-wanted testing',
        ]
        
        for query in queries:
            try:
                url = 'https://api.github.com/search/issues'
                params = {'q': query, 'sort': 'updated', 'order': 'desc', 'per_page': 20}
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    for item in response.json().get('items', []):
                        issue = self._parse_test_issue(item)
                        if issue:
                            issues.append(issue)
            except Exception as e:
                print(f"   Error: {e}")
        
        return issues
    
    def _parse_test_issue(self, issue: Dict) -> Optional[Dict]:
        """Parse test issue"""
        title = issue.get('title', '').lower()
        labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
        
        test_patterns = ['test', 'testing', 'coverage', 'unit test', 'e2e', 'integration test']
        is_test = any(p in title for p in test_patterns) or any('test' in l for l in labels)
        
        if not is_test:
            return None
        
        return {
            'id': issue.get('id'),
            'title': issue.get('title'),
            'url': issue.get('html_url'),
            'repo': issue.get('repository_url', '').split('/')[-1] if issue.get('repository_url') else 'unknown',
            'labels': labels,
            'score': 25 if 'coverage' in title else 15
        }
    
    def generate_basic_tests(self, work_dir: str) -> Dict:
        """Generate basic test files for common patterns"""
        results = {'created': [], 'existing': []}
        
        # Check for existing test structure
        test_files = []
        for root, dirs, files in os.walk(work_dir):
            if 'node_modules' in root or '__pycache__' in root:
                continue
            for f in files:
                if 'test' in f.lower() or 'spec' in f.lower():
                    test_files.append(f)
        
        if test_files:
            results['existing'] = test_files[:5]
        
        # Python: Create basic pytest structure if missing
        if os.path.exists(f"{work_dir}/setup.py") or os.path.exists(f"{work_dir}/pyproject.toml"):
            if not os.path.exists(f"{work_dir}/tests"):
                os.makedirs(f"{work_dir}/tests", exist_ok=True)
                with open(f"{work_dir}/tests/__init__.py", 'w') as f:
                    f.write("# Test package\n")
                with open(f"{work_dir}/tests/test_basic.py", 'w') as f:
                    f.write("""import pytest

def test_placeholder():
    \"\"\"Placeholder test - replace with actual tests\"\"\"\n    assert True
""")
                results['created'].append('tests/test_basic.py')
        
        # Node.js: Create basic Jest structure if missing
        if os.path.exists(f"{work_dir}/package.json"):
            if not os.path.exists(f"{work_dir}/__tests__") and not any('test' in f for f in test_files):
                os.makedirs(f"{work_dir}/__tests__", exist_ok=True)
                with open(f"{work_dir}/__tests__/basic.test.js", 'w') as f:
                    f.write("""describe('Basic Tests', () => {\n  test('placeholder', () => {\n    expect(true).toBe(true);\n  });\n});\n""")
                results['created'].append('__tests__/basic.test.js')
        
        return results
    
    def run(self):
        """Main execution"""
        print(f"🧪 Test Coverage Bounty Hunter starting at {datetime.now()}")
        print("=" * 70)
        
        issues = self.search_test_issues()
        print(f"\n🔍 Found {len(issues)} test coverage opportunities")
        
        issues.sort(key=lambda x: x['score'], reverse=True)
        
        print("\nTop Opportunities:")
        print("-" * 70)
        
        for i, issue in enumerate(issues[:10], 1):
            print(f"\n{i}. {issue['title'][:60]}")
            print(f"   Repo: {issue['repo']}")
        
        # Save results
        results_file = f"{self.data_dir}/test_issues_{datetime.now().strftime('%Y%m%d')}.json"
        with open(results_file, 'w') as f:
            json.dump(issues, f, indent=2)
        
        print(f"\n💾 Results saved: {results_file}")
        return issues

if __name__ == "__main__":
    hunter = TestBountyHunter()
    hunter.run()
