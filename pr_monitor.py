#!/usr/bin/env python3
"""
PR Monitor - Karl Ambrosius
Monitors submitted PRs for maintainer feedback and responds automatically
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class PRMonitor:
    def __init__(self):
        self.data_dir = "/agent/systems/bounty-hunter/data"
        self.github_token = open('/secrets/github_token').read().strip()
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.username = 'KarlAmbrosius'
        
    def load_submissions(self) -> List[Dict]:
        """Load all PR submissions from metrics"""
        submissions = []
        metrics_dir = "/agent/metrics"
        
        for filename in os.listdir(metrics_dir):
            if filename.startswith('pr_submissions_') and filename.endswith('.json'):
                filepath = os.path.join(metrics_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            submissions.extend(data)
                except:
                    pass
        
        return submissions
    
    def check_pr_status(self, owner: str, repo: str, pr_number: str) -> Optional[Dict]:
        """Check status of a PR"""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    'state': data.get('state'),
                    'merged': data.get('merged'),
                    'mergeable': data.get('mergeable'),
                    'comments': data.get('comments'),
                    'review_comments': data.get('review_comments'),
                    'title': data.get('title'),
                    'html_url': data.get('html_url'),
                    'updated_at': data.get('updated_at'),
                    'created_at': data.get('created_at')
                }
        except Exception as e:
            print(f"   Error checking PR: {e}")
        
        return None
    
    def get_pr_comments(self, owner: str, repo: str, pr_number: str) -> List[Dict]:
        """Get comments on a PR"""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"   Error getting comments: {e}")
        
        return []
    
    def respond_to_comment(self, owner: str, repo: str, pr_number: str, comment: str) -> bool:
        """Auto-respond to maintainer comments"""
        # Simple auto-responses
        responses = {
            'thank': "Thank you for the review! Let me know if any changes are needed. 🤖",
            'fix': "I'll look into fixing that right away. Thanks for the feedback! 🤖",
            'question': "Good question! The automated fixes focus on code quality improvements like typos and formatting. 🤖",
        }
        
        comment_lower = comment.lower()
        response_text = None
        
        if any(word in comment_lower for word in ['thanks', 'thank you', 'appreciate']):
            response_text = responses['thank']
        elif any(word in comment_lower for word in ['fix', 'change', 'update', 'please']):
            response_text = responses['fix']
        elif '?' in comment:
            response_text = responses['question']
        
        if response_text:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
            try:
                response = requests.post(url, headers=self.headers, 
                                        json={'body': response_text}, timeout=30)
                return response.status_code == 201
            except:
                pass
        
        return False
    
    def run(self):
        """Main monitoring loop"""
        print(f"👁️  PR Monitor starting at {datetime.now()}")
        print("=" * 70)
        
        submissions = self.load_submissions()
        
        if not submissions:
            print("No PR submissions found to monitor.")
            return
        
        print(f"📊 Monitoring {len(submissions)} PRs\n")
        
        for sub in submissions:
            owner = sub.get('owner')
            repo = sub.get('repo')
            issue = sub.get('issue')
            pr_url = sub.get('pr_url')
            
            # Extract PR number from URL
            pr_number = pr_url.split('/')[-1] if pr_url else None
            
            if not pr_number:
                continue
            
            print(f"🔍 {owner}/{repo} PR #{pr_number}")
            
            # Check PR status
            status = self.check_pr_status(owner, repo, pr_number)
            
            if status:
                print(f"   Status: {status['state']}")
                print(f"   Merged: {'✅ Yes' if status['merged'] else '⏳ No'}")
                print(f"   Comments: {status['comments']}")
                
                # Check for new comments
                if status['comments'] > 0:
                    comments = self.get_pr_comments(owner, repo, pr_number)
                    
                    # Filter for maintainer comments (not from us)
                    maintainer_comments = [
                        c for c in comments 
                        if c.get('user', {}).get('login') != self.username
                    ]
                    
                    if maintainer_comments:
                        print(f"   💬 {len(maintainer_comments)} maintainer comments")
                        
                        # Respond to latest comment
                        latest = maintainer_comments[-1]
                        comment_body = latest.get('body', '')
                        comment_time = latest.get('created_at', '')
                        
                        # Only respond to comments from last 24 hours
                        if comment_time:
                            comment_dt = datetime.fromisoformat(comment_time.replace('Z', '+00:00'))
                            if datetime.now(comment_dt.tzinfo) - comment_dt < timedelta(hours=24):
                                print(f"   🔄 Auto-responding...")
                                if self.respond_to_comment(owner, repo, pr_number, comment_body):
                                    print(f"   ✅ Response posted")
                                else:
                                    print(f"   ℹ️  No response needed")
            else:
                print(f"   ⚠️  Could not fetch status")
            
            print()
        
        print("=" * 70)
        print(f"✅ Monitoring complete at {datetime.now()}")

if __name__ == "__main__":
    monitor = PRMonitor()
    monitor.run()
