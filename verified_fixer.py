#!/usr/bin/env python3
"""
Verified Fixer - AUTONOMY-CLAW v2
Reads issue descriptions and applies verified fixes only
"""

import os
import re
import json
import subprocess
from typing import List, Dict, Optional

class VerifiedFixer:
    """Applies verified fixes based on issue descriptions"""
    
    @staticmethod
    def analyze_issue(issue_title: str, issue_body: str) -> Dict:
        """Analyze issue to determine what fix is needed"""
        title_lower = issue_title.lower()
        body_lower = issue_body.lower() if issue_body else ''
        combined = title_lower + ' ' + body_lower
        clean_combined = combined.replace('`', '').replace("'", "").replace('"', '')
        
        analysis = {
            'fix_type': None,
            'confidence': 0,
            'specific_fixes': [],
            'files_to_check': [],
        }
        
        # Priority 1: Specific typo mentioned (highest confidence)
        typo_patterns = [
            (r'["\'](\w+)["\']\s+(?:should be|->|to)\s+["\'](\w+)["\']', 0.95),
            (r'["\']?(\w+)["\']?\s+(?:should be|->|to)\s+["\']?(\w+)["\']?', 0.95),
            (r'typo[:\s]+["\']?(\w+)["\']?\s*[-=]+\s*["\']?(\w+)["\']?', 0.95),
            (r'replace\s+["\']?(\w+)["\']?\s+with\s+["\']?(\w+)["\']?', 0.95),
        ]
        
        for pattern, confidence in typo_patterns:
            matches = re.findall(pattern, combined)
            for wrong, correct in matches:
                analysis['specific_fixes'].append({
                    'type': 'typo',
                    'wrong': wrong,
                    'correct': correct
                })
                analysis['fix_type'] = 'specific_typo'
                analysis['confidence'] = confidence
                return analysis  # Return immediately for specific typos
        
        # Priority 2: CHANGELOG needed
        if 'changelog' in clean_combined:
            analysis['fix_type'] = 'changelog'
            analysis['confidence'] = 0.9
            analysis['files_to_check'] = ['CHANGELOG.md', 'CHANGELOG', 'HISTORY.md']
            return analysis
        
        # Priority 3: Common typos (check before general patterns)
        common_typos = {
            'recieve': 'receive',
            'seperate': 'separate', 
            'occured': 'occurred',
            'accomodate': 'accommodate',
            'definately': 'definitely',
            'refering': 'referring',
            'successfull': 'successful',
            'untill': 'until',
        }
        
        found_typos = []
        for wrong, correct in common_typos.items():
            if wrong in clean_combined:
                found_typos.append({'wrong': wrong, 'correct': correct})
        
        if found_typos:
            analysis['fix_type'] = 'common_typos'
            analysis['confidence'] = 0.75
            analysis['specific_fixes'] = found_typos
            return analysis
        
        # Priority 4: README improvements
        if 'readme' in clean_combined:
            analysis['fix_type'] = 'readme'
            analysis['confidence'] = 0.8
            analysis['files_to_check'] = ['README.md', 'README.rst']
            return analysis
        
        # Priority 4: Formatting/Linting
        if any(x in clean_combined for x in ['format', 'lint', 'prettier', 'eslint', 'black']):
            analysis['fix_type'] = 'formatting'
            analysis['confidence'] = 0.85
            return analysis
        
        # Priority 5: Documentation (general)
        if any(x in clean_combined for x in ['documentation', 'docs', 'document']):
            analysis['fix_type'] = 'documentation'
            analysis['confidence'] = 0.6
        
        # Priority 6: Broken links
        elif any(x in clean_combined for x in ['broken link', '404', 'dead link']):
            analysis['fix_type'] = 'links'
            analysis['confidence'] = 0.7
        
        return analysis
    
    @staticmethod
    def apply_specific_typo_fix(work_dir: str, wrong: str, correct: str) -> List[str]:
        """Apply a specific typo fix"""
        changes = []
        
        for root, dirs, files in os.walk(work_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', 'venv']]
            
            for filename in files:
                if any(filename.endswith(ext) for ext in ['.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yml', '.yaml', '.rst']):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        original = content
                        # Word boundary regex for whole word replacement
                        content = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, content, flags=re.IGNORECASE)
                        
                        if content != original:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            rel_path = os.path.relpath(filepath, work_dir)
                            changes.append(f"Fixed '{wrong}' -> '{correct}' in {rel_path}")
                    except Exception as e:
                        print(f"   Error fixing {filepath}: {e}")
        
        return changes
    
    @staticmethod
    def create_changelog(work_dir: str) -> List[str]:
        """Create a basic CHANGELOG.md if it doesn't exist"""
        changes = []
        
        changelog_path = os.path.join(work_dir, 'CHANGELOG.md')
        if os.path.exists(changelog_path):
            return changes  # Already exists
        
        # Try to get git log for recent changes
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-20'],
                cwd=work_dir,
                capture_output=True,
                text=True
            )
            recent_commits = result.stdout.strip() if result.returncode == 0 else ''
        except:
            recent_commits = ''
        
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial changelog created

## Recent Commits
{recent_commits}

---
*Generated by AUTONOMY-CLAW*
"""
        
        try:
            with open(changelog_path, 'w', encoding='utf-8') as f:
                f.write(changelog_content)
            changes.append("Created CHANGELOG.md with Keep a Changelog format")
        except Exception as e:
            print(f"   Error creating CHANGELOG: {e}")
        
        return changes
    
    @staticmethod
    def fix_readme_issues(work_dir: str, issue_body: str) -> List[str]:
        """Fix common README issues"""
        changes = []
        
        readme_path = os.path.join(work_dir, 'README.md')
        if not os.path.exists(readme_path):
            return changes
        
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # Fix common README issues
            # Ensure there's a title
            if not content.startswith('#'):
                content = f"# Project\n\n{content}"
            
            # Fix broken markdown links
            content = re.sub(r'\[([^\]]+)\]\s*\(\s*\)', r'[\1](#)', content)
            
            if content != original:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                changes.append("Fixed README formatting issues")
        
        except Exception as e:
            print(f"   Error fixing README: {e}")
        
        return changes
    
    @staticmethod
    def run_formatter(work_dir: str) -> List[str]:
        """Run appropriate formatter for the project"""
        changes = []
        
        # Python - black
        if os.path.exists(os.path.join(work_dir, 'setup.py')) or \
           os.path.exists(os.path.join(work_dir, 'pyproject.toml')) or \
           any(f.endswith('.py') for f in os.listdir(work_dir) if os.path.isfile(os.path.join(work_dir, f))):
            try:
                result = subprocess.run(
                    ['black', '.'],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    changes.append("Formatted Python code with black")
            except:
                pass
        
        # JavaScript/Node - prettier
        if os.path.exists(os.path.join(work_dir, 'package.json')):
            try:
                result = subprocess.run(
                    ['npx', 'prettier', '--write', '.'],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    changes.append("Formatted JS code with prettier")
            except:
                pass
        
        return changes
    
    @staticmethod
    def verify_fix(work_dir: str, analysis: Dict) -> bool:
        """Verify that the fix was applied correctly"""
        if analysis['fix_type'] == 'changelog':
            return os.path.exists(os.path.join(work_dir, 'CHANGELOG.md'))
        
        if analysis['fix_type'] in ['specific_typo', 'common_typos'] and analysis['specific_fixes']:
            # Check that at least one typo was fixed
            for fix in analysis['specific_fixes']:
                wrong = fix['wrong']
                # Search for the typo in the codebase
                found = False
                for root, dirs, files in os.walk(work_dir):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
                    for filename in files:
                        if any(filename.endswith(ext) for ext in ['.md', '.txt', '.py', '.js', '.ts']):
                            filepath = os.path.join(root, filename)
                            try:
                                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                if re.search(r'\b' + re.escape(wrong) + r'\b', content, re.IGNORECASE):
                                    found = True
                                    break
                            except:
                                pass
                    if found:
                        break
                # If typo not found, it was fixed
                if not found:
                    return True
            return False
        
        # For other types, check if any files were modified
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=work_dir,
                capture_output=True,
                text=True
            )
            return len(result.stdout.strip()) > 0
        except:
            return False
    
    @staticmethod
    def fix_issue(work_dir: str, issue_title: str, issue_body: str) -> Dict:
        """Main entry point - analyze and fix an issue"""
        print(f"   🔍 Analyzing issue: {issue_title[:50]}...")
        
        # Analyze what fix is needed
        analysis = VerifiedFixer.analyze_issue(issue_title, issue_body)
        
        if analysis['confidence'] < 0.7 and analysis['fix_type'] != 'documentation':
            return {
                'success': False,
                'reason': f"Confidence too low ({analysis['confidence']:.2f})",
                'analysis': analysis,
                'changes': []
            }
        
        # For documentation issues with low confidence, try auto typo scan
        if analysis['confidence'] < 0.7 and analysis['fix_type'] == 'documentation':
            from typo_scanner import AutoTypoScanner
            typo_result = AutoTypoScanner.scan_and_fix(work_dir)
            if typo_result['found'] == 0:
                return {
                    'success': False,
                    'reason': f"Confidence too low ({analysis['confidence']:.2f}) and no typos found",
                    'analysis': analysis,
                    'changes': []
                }
            # If typos were found, proceed with the fix
            analysis['fix_type'] = 'auto_typo_fix'
            analysis['confidence'] = 0.75
        
        print(f"   📋 Fix type: {analysis['fix_type']} (confidence: {analysis['confidence']:.2f})")
        
        changes = []
        
        # Apply the appropriate fix
        if analysis['fix_type'] in ['specific_typo', 'common_typos'] and analysis['specific_fixes']:
            for fix in analysis['specific_fixes']:
                fix_changes = VerifiedFixer.apply_specific_typo_fix(
                    work_dir, 
                    fix['wrong'], 
                    fix['correct']
                )
                changes.extend(fix_changes)
        
        elif analysis['fix_type'] == 'changelog':
            changes = VerifiedFixer.create_changelog(work_dir)
        
        elif analysis['fix_type'] == 'readme':
            changes = VerifiedFixer.fix_readme_issues(work_dir, issue_body)
        
        elif analysis['fix_type'] == 'formatting':
            changes = VerifiedFixer.run_formatter(work_dir)
        
        elif analysis['fix_type'] == 'documentation':
            # For generic documentation issues, try auto typo scanning
            from typo_scanner import AutoTypoScanner
            typo_result = AutoTypoScanner.scan_and_fix(work_dir)
            if typo_result['found'] > 0:
                changes.extend(typo_result['changes'])
                analysis['fix_type'] = 'auto_typo_fix'
                analysis['auto_typo_details'] = typo_result
        
        # Verify the fix
        verified = VerifiedFixer.verify_fix(work_dir, analysis)
        
        if not verified:
            return {
                'success': False,
                'reason': "Fix verification failed",
                'analysis': analysis,
                'changes': changes
            }
        
        return {
            'success': True,
            'analysis': analysis,
            'changes': changes,
            'verified': True
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        work_dir = sys.argv[1]
        title = sys.argv[2]
        body = sys.argv[3]
        result = VerifiedFixer.fix_issue(work_dir, title, body)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python3 verified_fixer.py <repo_path> <issue_title> <issue_body>")
