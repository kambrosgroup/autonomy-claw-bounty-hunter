#!/usr/bin/env python3
"""
Translation/Localization Bounty Hunter - Karl Ambrosius
Finds i18n opportunities and helps with translations
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional

class TranslationBountyHunter:
    """Hunts for translation and localization opportunities"""
    
    def __init__(self):
        self.data_dir = "/agent/systems/bounty-hunter/translation"
        os.makedirs(self.data_dir, exist_ok=True)
        self.github_token = open('/secrets/github_token').read().strip()
        self.headers = {'Authorization': f'token {self.github_token}', 'Accept': 'application/vnd.github.v3+json'}
        
    def search_translation_issues(self) -> List[Dict]:
        """Search for translation-related issues"""
        issues = []
        
        queries = [
            'is:issue is:open label:translation',
            'is:issue is:open label:i18n',
            'is:issue is:open label:localization',
            'is:issue is:open "add translation"',
            'is:issue is:open "missing translation"',
        ]
        
        for query in queries:
            try:
                url = 'https://api.github.com/search/issues'
                params = {'q': query, 'sort': 'updated', 'order': 'desc', 'per_page': 20}
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    for item in response.json().get('items', []):
                        issue = self._parse_translation_issue(item)
                        if issue:
                            issues.append(issue)
            except Exception as e:
                print(f"   Error: {e}")
        
        return issues
    
    def _parse_translation_issue(self, issue: Dict) -> Optional[Dict]:
        """Parse translation issue"""
        title = issue.get('title', '').lower()
        labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
        
        i18n_patterns = ['translation', 'i18n', 'localization', 'locale', 'language']
        is_i18n = any(p in title for p in i18n_patterns) or any(l in ['translation', 'i18n', 'localization'] for l in labels)
        
        if not is_i18n:
            return None
        
        # Extract language if mentioned
        languages = ['chinese', 'spanish', 'french', 'german', 'japanese', 'korean', 'russian', 'portuguese']
        mentioned_lang = [l for l in languages if l in title]
        
        return {
            'id': issue.get('id'),
            'title': issue.get('title'),
            'url': issue.get('html_url'),
            'repo': issue.get('repository_url', '').split('/')[-1] if issue.get('repository_url') else 'unknown',
            'labels': labels,
            'language': mentioned_lang[0] if mentioned_lang else None,
            'score': 20 if mentioned_lang else 10
        }
    
    def run(self):
        """Main execution"""
        print(f"🌐 Translation Bounty Hunter starting at {datetime.now()}")
        print("=" * 70)
        
        issues = self.search_translation_issues()
        print(f"\n🔍 Found {len(issues)} translation opportunities")
        
        issues.sort(key=lambda x: x['score'], reverse=True)
        
        print("\nTop Opportunities:")
        print("-" * 70)
        
        for i, issue in enumerate(issues[:10], 1):
            print(f"\n{i}. {issue['title'][:60]}")
            print(f"   Repo: {issue['repo']}")
            if issue.get('language'):
                print(f"   Language: {issue['language']}")
        
        # Save results
        results_file = f"{self.data_dir}/translation_issues_{datetime.now().strftime('%Y%m%d')}.json"
        with open(results_file, 'w') as f:
            json.dump(issues, f, indent=2)
        
        print(f"\n💾 Results saved: {results_file}")
        return issues

if __name__ == "__main__":
    hunter = TranslationBountyHunter()
    hunter.run()
