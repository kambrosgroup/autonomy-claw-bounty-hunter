#!/usr/bin/env python3
"""
Smart Fixer - AUTONOMY-CLAW Bounty Hunter Module
Implements intelligent fixes for common issue types
"""

import os
import re
import json
from typing import List, Dict, Tuple

class SmartFixer:
    """Intelligent code fixer for common GitHub issues"""
    
    COMMON_TYPOS = {
        'recieve': 'receive',
        'seperate': 'separate',
        'occured': 'occurred',
        'accomodate': 'accommodate',
        'definately': 'definitely',
        'goverment': 'government',
        'occurence': 'occurrence',
        'refering': 'referring',
        'successfull': 'successful',
        'untill': 'until',
    }
    
    @staticmethod
    def find_typos_in_repo(work_dir: str) -> List[Dict]:
        """Scan repository for common typos"""
        findings = []
        
        for root, dirs, files in os.walk(work_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for filename in files:
                if any(filename.endswith(ext) for ext in ['.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx']):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines, 1):
                            for typo, correction in SmartFixer.COMMON_TYPOS.items():
                                if typo in line.lower():
                                    findings.append({
                                        'file': os.path.relpath(filepath, work_dir),
                                        'line': i,
                                        'typo': typo,
                                        'correction': correction,
                                        'context': line.strip()[:80]
                                    })
                    except:
                        pass
        
        return findings
    
    @staticmethod
    def fix_typos(work_dir: str, findings: List[Dict]) -> int:
        """Fix found typos"""
        fixed_count = 0
        
        # Group by file
        by_file = {}
        for f in findings:
            filepath = os.path.join(work_dir, f['file'])
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append(f)
        
        for filepath, file_findings in by_file.items():
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                original = content
                for finding in file_findings:
                    # Case-insensitive replace preserving case
                    typo = finding['typo']
                    correction = finding['correction']
                    
                    # Simple replace (could be enhanced for case preservation)
                    content = re.sub(r'\b' + typo + r'\b', correction, content, flags=re.IGNORECASE)
                
                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_count += len(file_findings)
            except Exception as e:
                print(f"Error fixing {filepath}: {e}")
        
        return fixed_count
    
    @staticmethod
    def fix_trailing_whitespace(work_dir: str) -> int:
        """Remove trailing whitespace from files"""
        fixed_count = 0
        
        for root, dirs, files in os.walk(work_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for filename in files:
                if any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.txt']):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        new_lines = [line.rstrip() + '\n' if line.rstrip() else '\n' for line in lines]
                        # Remove trailing empty lines
                        while new_lines and new_lines[-1].strip() == '':
                            new_lines.pop()
                        if new_lines:
                            new_lines[-1] = new_lines[-1].rstrip() + '\n'
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                        
                        fixed_count += 1
                    except:
                        pass
        
        return fixed_count
    
    @staticmethod
    def add_missing_newlines(work_dir: str) -> int:
        """Ensure files end with newline"""
        fixed_count = 0
        
        for root, dirs, files in os.walk(work_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for filename in files:
                if any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.sh', '.yml', '.yaml']):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'rb') as f:
                            content = f.read()
                        
                        if content and not content.endswith(b'\n'):
                            with open(filepath, 'ab') as f:
                                f.write(b'\n')
                            fixed_count += 1
                    except:
                        pass
        
        return fixed_count
    
    @staticmethod
    def run_all_fixes(work_dir: str) -> Dict:
        """Run all automated fixes"""
        results = {
            'typos_found': [],
            'typos_fixed': 0,
            'trailing_ws_fixed': 0,
            'newlines_added': 0,
            'total_changes': 0
        }
        
        # Find and fix typos
        print("   🔍 Scanning for typos...")
        typos = SmartFixer.find_typos_in_repo(work_dir)
        if typos:
            print(f"   📋 Found {len(typos)} typos")
            results['typos_found'] = typos[:10]  # Store first 10
            results['typos_fixed'] = SmartFixer.fix_typos(work_dir, typos)
        
        # Fix trailing whitespace
        print("   🔍 Fixing trailing whitespace...")
        results['trailing_ws_fixed'] = SmartFixer.fix_trailing_whitespace(work_dir)
        
        # Add missing newlines
        print("   🔍 Adding missing newlines...")
        results['newlines_added'] = SmartFixer.add_missing_newlines(work_dir)
        
        results['total_changes'] = (
            results['typos_fixed'] + 
            results['trailing_ws_fixed'] + 
            results['newlines_added']
        )
        
        return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        work_dir = sys.argv[1]
        results = SmartFixer.run_all_fixes(work_dir)
        print(json.dumps(results, indent=2))
    else:
        print("Usage: python3 smart_fixer.py <repo_path>")
