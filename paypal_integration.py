#!/usr/bin/env python3
"""
PayPal Integration Module - Karl Ambrosius
Handles PayPal payments for bounty earnings
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional

class PayPalIntegration:
    """PayPal integration for receiving bounty payments"""
    
    def __init__(self):
        self.client_id = os.getenv('PAYPAL_CLIENT_ID') or self._read_secret('paypal_client_id')
        self.client_secret = os.getenv('PAYPAL_SECRET') or self._read_secret('paypal_secret')
        self.paypal_email = "karlambrosius@outlook.com.au"
        
        # PayPal API endpoints
        self.base_url = "https://api-m.sandbox.paypal.com"  # Use sandbox for testing
        # self.base_url = "https://api-m.paypal.com"  # Production
        
        self.access_token = None
        
    def _read_secret(self, name: str) -> Optional[str]:
        """Read secret from file"""
        path = f'/secrets/{name}'
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read().strip()
        return None
    
    def get_access_token(self) -> bool:
        """Get PayPal access token"""
        if not self.client_id or not self.client_secret:
            print("❌ PayPal credentials not configured")
            return False
        
        url = f"{self.base_url}/v1/oauth2/token"
        
        try:
            response = requests.post(
                url,
                auth=(self.client_id, self.client_secret),
                data={'grant_type': 'client_credentials'},
                timeout=30
            )
            
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                return True
            else:
                print(f"❌ PayPal auth failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ PayPal error: {e}")
            return False
    
    def create_payout(self, amount: float, currency: str = "USD", note: str = "Bounty Payment") -> Dict:
        """Create a payout to Karl's PayPal account"""
        if not self.access_token:
            if not self.get_access_token():
                return {'success': False, 'error': 'Authentication failed'}
        
        url = f"{self.base_url}/v1/payments/payouts"
        
        payload = {
            "sender_batch_header": {
                "sender_batch_id": f"bounty_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "email_subject": "GitHub Bounty Payment",
                "email_message": f"Payment for completed GitHub bounty work. {note}"
            },
            "items": [{
                "recipient_type": "EMAIL",
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": currency
                },
                "receiver": self.paypal_email,
                "note": note,
                "sender_item_id": f"item_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }]
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'batch_id': data.get('batch_header', {}).get('payout_batch_id'),
                    'amount': amount,
                    'currency': currency,
                    'receiver': self.paypal_email
                }
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def track_earnings(self, amount: float, source: str, pr_url: str):
        """Track bounty earnings for reporting"""
        earnings_data = {
            'timestamp': datetime.now().isoformat(),
            'amount': amount,
            'currency': 'USD',
            'source': source,
            'pr_url': pr_url,
            'paypal_email': self.paypal_email,
            'status': 'pending_payout'
        }
        
        # Save to earnings log
        log_file = '/agent/metrics/bounty_earnings.jsonl'
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(f"{json.dumps(earnings_data)}\n")
        
        print(f"💰 Tracked ${amount} earnings for {source}")
        print(f"   PayPal: {self.paypal_email}")
        
        return earnings_data
    
    def generate_payout_report(self) -> str:
        """Generate a report of pending payouts"""
        log_file = '/agent/metrics/bounty_earnings.jsonl'
        
        if not os.path.exists(log_file):
            return "No earnings recorded yet."
        
        total_pending = 0
        pending_items = []
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('status') == 'pending_payout':
                        total_pending += data.get('amount', 0)
                        pending_items.append(data)
                except:
                    pass
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           PAYPAL PAYOUT REPORT - Karl Ambrosius              ║
╚══════════════════════════════════════════════════════════════╝

PayPal Account: {self.paypal_email}

📊 PENDING PAYOUTS
────────────────────────────────────────────────────────────────
Total Pending: ${total_pending:.2f}
Number of Items: {len(pending_items)}

📋 ITEMS
────────────────────────────────────────────────────────────────
"""
        
        for item in pending_items[-10:]:  # Show last 10
            report += f"""
${item['amount']:.2f} - {item['source'][:40]}
   {item['pr_url']}
   Date: {item['timestamp'][:10]}
"""
        
        report += f"""
────────────────────────────────────────────────────────────────
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To request payout, contact: karlambrosius@outlook.com.au
"""
        
        return report

if __name__ == "__main__":
    paypal = PayPalIntegration()
    
    # Show current config
    print("PayPal Configuration:")
    print(f"  Email: {paypal.paypal_email}")
    print(f"  Client ID: {'✅ Configured' if paypal.client_id else '❌ Missing'}")
    print(f"  Client Secret: {'✅ Configured' if paypal.client_secret else '❌ Missing'}")
    
    # Generate report
    print("\n" + paypal.generate_payout_report())
