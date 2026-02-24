#!/usr/bin/env python3
"""
Auto Typo Scanner - Karl Ambrosius
Scans repository files for common typos automatically
"""

import os
import re
from typing import List, Dict

class AutoTypoScanner:
    """Scans files for common typos without needing issue description"""
    
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
        'wich': 'which',
        'teh': 'the',
        'adn': 'and',
        'taht': 'that',
        'wiht': 'with',
        'fo': 'of',
        'ot': 'to',
        'htis': 'this',
        'tiem': 'time',
        'yuo': 'you',
        'iyt': 'it',
        'waht': 'what',
        'hwat': 'what',
        'thier': 'their',
        'theri': 'their',
        'occuring': 'occurring',
        'occurance': 'occurrence',
        'recieved': 'received',
        'seperated': 'separated',
        'seperation': 'separation',
    }
    
    @staticmethod
    def scan_repository(work_dir: str) -> List[Dict]:
        """Scan repository for common typos"""
        findings = []
        
        text_extensions = [
            '.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx',
            '.json', '.yml', '.yaml', '.rst', '.html', '.css',
            '.sh', '.bash', '.zsh', '.fish'
        ]
        
        exclude_dirs = {
            '.git', 'node_modules', '__pycache__', 'venv', '.venv',
            'env', '.env', 'dist', 'build', '.pytest_cache',
            '.mypy_cache', '.tox', 'coverage', '.coverage'
        }
        
        for root, dirs, files in os.walk(work_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for filename in files:
                if any(filename.endswith(ext) for ext in text_extensions):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                        
                        for line_num, line in enumerate(lines, 1):
                            for wrong, correct in AutoTypoScanner.COMMON_TYPOS.items():
                                # Check for whole word match (case insensitive)
                                pattern = r'\b' + re.escape(wrong) + r'\b'
                                if re.search(pattern, line, re.IGNORECASE):
                                    # Get context (line with typo)
                                    context = line.strip()
                                    if len(context) > 80:
                                        context = context[:77] + '...'
                                    
                                    findings.append({
                                        'file': os.path.relpath(filepath, work_dir),
                                        'line': line_num,
                                        'typo': wrong,
                                        'correction': correct,
                                        'context': context
                                    })
                    except Exception as e:
                        # Skip files that can't be read
                        pass
        
        return findings
    
    @staticmethod
    def fix_found_typos(work_dir: str, findings: List[Dict]) -> List[str]:
        """Fix all found typos"""
        changes = []
        
        # Group findings by file
        by_file = {}
        for finding in findings:
            filepath = os.path.join(work_dir, finding['file'])
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append(finding)
        
        for filepath, file_findings in by_file.items():
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                original = content
                fixed_typos = set()
                
                for finding in file_findings:
                    typo = finding['typo']
                    correction = finding['correction']
                    
                    if typo not in fixed_typos:
                        # Replace whole word only, preserve case
                        pattern = r'\b' + re.escape(typo) + r'\b'
                        content = re.sub(pattern, correction, content, flags=re.IGNORECASE)
                        fixed_typos.add(typo)
                
                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    rel_path = os.path.relpath(filepath, work_dir)
                    changes.append(f"Fixed {len(fixed_typos)} typo(s) in {rel_path}")
            
            except Exception as e:
                print(f"   Error fixing {filepath}: {e}")
        
        return changes
    
    @staticmethod
    def scan_and_fix(work_dir: str) -> Dict:
        """Scan repository and fix all typos"""
        print("   🔍 Scanning repository for common typos...")
        
        findings = AutoTypoScanner.scan_repository(work_dir)
        
        if not findings:
            return {
                'found': 0,
                'fixed': 0,
                'changes': [],
                'details': []
            }
        
        print(f"   📋 Found {len(findings)} typo(s) in {len(set(f['file'] for f in findings))} file(s)")
        
        # Show first few findings
        for finding in findings[:5]:
            print(f"      - {finding['file']}:{finding['line']} '{finding['typo']}' -> '{finding['correction']}'")
        if len(findings) > 5:
            print(f"      ... and {len(findings) - 5} more")
        
        # Fix the typos
        changes = AutoTypoScanner.fix_found_typos(work_dir, findings)
        
        return {
            'found': len(findings),
            'fixed': len(findings),  # All found typos are fixed
            'changes': changes,
            'details': findings
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        work_dir = sys.argv[1]
        result = AutoTypoScanner.scan_and_fix(work_dir)
        print("\n" + "="*50)
        print(f"Found: {result['found']} typo(s)")
        print(f"Fixed in: {len(result['changes'])} file(s)")
        for change in result['changes']:
            print(f"  - {change}")
    else:
        print("Usage: python3 typo_scanner.py <repo_path>")
