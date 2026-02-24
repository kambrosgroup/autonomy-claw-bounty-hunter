#!/usr/bin/env python3
"""
Container Entry Point - Karl Ambrosius
Main entry point for Docker container
"""

import os
import sys

def main():
    print("=" * 70)
    print("🚀 Karl Ambrosius - Bounty Hunter Container")
    print("=" * 70)
    print("👤 Karl Ambrosius")
    print("💰 PayPal: karlambrosius@outlook.com.au")
    print("=" * 70)
    
    # Check environment
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("\n❌ ERROR: GITHUB_TOKEN not set")
        print("Please set the GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    print(f"\n✅ GITHUB_TOKEN configured")
    print(f"✅ REPOS_DIR: {os.getenv('REPOS_DIR', '/tmp/bounty-repos')}")
    
    # Try to run batch submitter
    scripts_to_try = [
        'scripts/batch_submitter.py',
        'batch_submitter.py',
        '/app/scripts/batch_submitter.py',
        '/app/batch_submitter.py',
    ]
    
    for script in scripts_to_try:
        if os.path.exists(script):
            print(f"\n🎯 Running: {script}")
            os.system(f"python3 {script}")
            return
    
    # If no script found, try mega processor
    mega_scripts = [
        'mega_batch_processor.py',
        '/app/mega_batch_processor.py',
    ]
    
    for script in mega_scripts:
        if os.path.exists(script):
            print(f"\n🎯 Running: {script}")
            os.system(f"python3 {script}")
            return
    
    print("\n❌ No processor scripts found!")
    print("Available files in /app:")
    os.system("ls -la /app/")
    sys.exit(1)

if __name__ == "__main__":
    main()
