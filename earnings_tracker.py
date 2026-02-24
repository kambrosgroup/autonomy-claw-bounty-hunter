#!/usr/bin/env python3
"""
Karl Ambrosius Earnings Tracker
Tracks revenue from all sources
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class EarningsTracker:
    def __init__(self):
        self.metrics_dir = "/agent/metrics"
        self.earnings_file = f"{self.metrics_dir}/bounty_earnings.jsonl"
        
    def load_earnings(self):
        """Load all earnings data"""
        earnings = []
        if os.path.exists(self.earnings_file):
            with open(self.earnings_file, 'r') as f:
                for line in f:
                    try:
                        earnings.append(json.loads(line.strip()))
                    except:
                        pass
        return earnings
    
    def calculate_stats(self):
        """Calculate earnings statistics"""
        earnings = self.load_earnings()
        
        stats = {
            'total_earned': 0,
            'total_prs_merged': len(earnings),
            'by_repo': defaultdict(int),
            'by_month': defaultdict(int),
            'by_week': defaultdict(int),
            'projections': {}
        }
        
        for entry in earnings:
            amount = entry.get('estimated_value', 0)
            stats['total_earned'] += amount
            
            # By repo
            repo = entry.get('repo', 'unknown')
            stats['by_repo'][repo] += amount
            
            # By month
            try:
                date = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                month_key = date.strftime('%Y-%m')
                stats['by_month'][month_key] += amount
                
                # By week
                week_key = date.strftime('%Y-W%U')
                stats['by_week'][week_key] += amount
            except:
                pass
        
        # Calculate projections
        if stats['by_week']:
            avg_weekly = sum(stats['by_week'].values()) / len(stats['by_week'])
            stats['projections'] = {
                'weekly_average': avg_weekly,
                'monthly_projection': avg_weekly * 4,
                'yearly_projection': avg_weekly * 52
            }
        
        return stats
    
    def generate_report(self):
        """Generate earnings report"""
        stats = self.calculate_stats()
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           Karl Ambrosius EARNINGS REPORT                      ║
╚══════════════════════════════════════════════════════════════╝

📊 SUMMARY
────────────────────────────────────────────────────────────────
Total Earned:        ${stats['total_earned']}
PRs Merged:          {stats['total_prs_merged']}
Avg per PR:          ${(stats['total_earned'] / stats['total_prs_merged']) if stats['total_prs_merged'] > 0 else 0:.2f}

📈 PROJECTIONS
────────────────────────────────────────────────────────────────
Weekly Average:      ${stats['projections'].get('weekly_average', 0):.2f}
Monthly Projection:  ${stats['projections'].get('monthly_projection', 0):.2f}
Yearly Projection:   ${stats['projections'].get('yearly_projection', 0):.2f}

💰 BY REPOSITORY
────────────────────────────────────────────────────────────────
"""
        
        for repo, amount in sorted(stats['by_repo'].items(), key=lambda x: x[1], reverse=True):
            report += f"{repo:40} ${amount}\n"
        
        report += """
📅 BY MONTH
────────────────────────────────────────────────────────────────
"""
        
        for month, amount in sorted(stats['by_month'].items()):
            report += f"{month:20} ${amount}\n"
        
        report += f"""
────────────────────────────────────────────────────────────────
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Next payout target: ${max(0, 100 - stats['total_earned'])}
"""
        
        return report
    
    def save_report(self):
        """Save report to file"""
        report = self.generate_report()
        
        report_file = f"{self.metrics_dir}/earnings_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Also save JSON stats
        stats = self.calculate_stats()
        stats_file = f"{self.metrics_dir}/earnings_stats.json"
        
        # Convert defaultdict to dict for JSON
        stats_json = {
            'total_earned': stats['total_earned'],
            'total_prs_merged': stats['total_prs_merged'],
            'by_repo': dict(stats['by_repo']),
            'by_month': dict(stats['by_month']),
            'by_week': dict(stats['by_week']),
            'projections': stats['projections'],
            'generated_at': datetime.now().isoformat()
        }
        
        with open(stats_file, 'w') as f:
            json.dump(stats_json, f, indent=2)
        
        print(report)
        print(f"\n✅ Report saved to {report_file}")
        print(f"✅ Stats saved to {stats_file}")
        
        return report

if __name__ == "__main__":
    tracker = EarningsTracker()
    tracker.save_report()
