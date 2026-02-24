#!/usr/bin/env python3
"""
Karl Ambrosius Webhook Server
Receives GitHub webhooks and triggers actions
"""

import os
import json
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class WebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming webhooks"""
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/webhook':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Verify signature (optional, requires WEBHOOK_SECRET)
            signature = self.headers.get('X-Hub-Signature-256')
            if signature and not self.verify_signature(body, signature):
                self.send_error(401, 'Invalid signature')
                return
            
            # Parse event
            event_type = self.headers.get('X-GitHub-Event', 'unknown')
            
            try:
                payload = json.loads(body)
                self.handle_event(event_type, payload)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok'}).encode())
                
            except Exception as e:
                print(f"Error handling webhook: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404)
    
    def verify_signature(self, body, signature):
        """Verify webhook signature"""
        secret = os.getenv('WEBHOOK_SECRET', '').encode()
        if not secret:
            return True  # Skip verification if no secret
        
        expected = 'sha256=' + hmac.new(secret, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    def handle_event(self, event_type, payload):
        """Handle different GitHub events"""
        print(f"\n[{datetime.now()}] Received {event_type} event")
        
        if event_type == 'pull_request':
            self.handle_pr_event(payload)
        elif event_type == 'issues':
            self.handle_issue_event(payload)
        elif event_type == 'issue_comment':
            self.handle_comment_event(payload)
        elif event_type == 'push':
            self.handle_push_event(payload)
        else:
            print(f"  Unhandled event type: {event_type}")
    
    def handle_pr_event(self, payload):
        """Handle pull request events"""
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        
        if action == 'closed' and pr.get('merged'):
            print(f"  🎉 PR MERGED!")
            print(f"     Repo: {payload['repository']['full_name']}")
            print(f"     PR: #{pr['number']} - {pr['title']}")
            print(f"     URL: {pr['html_url']}")
            
            # Log bounty earned
            self.log_bounty_earned(pr)
            
        elif action == 'opened':
            print(f"  📤 New PR opened: #{pr['number']}")
            
        elif action == 'synchronize':
            print(f"  📝 PR updated: #{pr['number']}")
    
    def handle_issue_event(self, payload):
        """Handle issue events"""
        action = payload.get('action')
        issue = payload.get('issue', {})
        
        if action == 'opened':
            labels = [l['name'] for l in issue.get('labels', [])]
            
            # Check if it's a bounty issue
            if any(l in labels for l in ['bounty', 'reward', 'good first issue']):
                print(f"  🎯 New bounty issue!")
                print(f"     Repo: {payload['repository']['full_name']}")
                print(f"     Issue: #{issue['number']} - {issue['title']}")
    
    def handle_comment_event(self, payload):
        """Handle comment events"""
        comment = payload.get('comment', {})
        issue = payload.get('issue', {})
        
        # Check if it's on one of our PRs
        if 'Karl Ambrosius' in issue.get('title', ''):
            print(f"  💬 Comment on our PR")
            print(f"     Author: {comment['user']['login']}")
            print(f"     Body: {comment['body'][:100]}...")
    
    def handle_push_event(self, payload):
        """Handle push events"""
        ref = payload.get('ref', '')
        if ref == 'refs/heads/main' or ref == 'refs/heads/master':
            commits = payload.get('commits', [])
            print(f"  🚀 {len(commits)} commit(s) pushed to main")
    
    def log_bounty_earned(self, pr):
        """Log when a bounty is earned"""
        bounty_data = {
            'timestamp': datetime.now().isoformat(),
            'pr_number': pr['number'],
            'pr_title': pr['title'],
            'pr_url': pr['html_url'],
            'repo': pr['base']['repo']['full_name'],
            'estimated_value': 30  # Conservative estimate
        }
        
        # Append to earnings log
        log_file = '/agent/metrics/bounty_earnings.jsonl'
        with open(log_file, 'a') as f:
            f.write(json.dumps(bounty_data) + '\n')
        
        print(f"  💰 Bounty logged! Est. value: ${bounty_data['estimated_value']}")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=8080):
    """Run the webhook server"""
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    print(f"🌐 Webhook server running on port {port}")
    print(f"   Endpoint: http://localhost:{port}/webhook")
    print(f"\nConfigure in GitHub:")
    print(f"   Settings → Webhooks → Add webhook")
    print(f"   Payload URL: http://YOUR_IP:{port}/webhook")
    print(f"   Content type: application/json")
    print(f"   Events: Pull requests, Issues, Issue comments, Pushes")
    print(f"\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
