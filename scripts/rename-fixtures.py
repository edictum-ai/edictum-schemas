#!/usr/bin/env python3
"""
Rename all fixture files from v1 terminology to v2.

Changes:
- contracts: -> rules:
- kind: ContractBundle -> kind: Ruleset  
- effect: deny -> action: block
- effect: approve -> action: ask
- effect: warn -> action: warn (unchanged value)
- effect: redact -> action: redact (unchanged value)
- effect: allow -> action: allow (unchanged value)
- timeout_effect: deny -> timeout_effect: block
- timeout_effect: allow -> timeout_effect: allow (unchanged value)
- outside: "deny" -> outside: "block"
- outside: "approve" -> outside: "ask"

Does NOT change:
- side_effect (different concept, not governance effect)
- type: pre/post/session/sandbox (stays)
- Anything inside description strings or injected payloads
"""

import os
import re
import sys
from pathlib import Path


def rename_fixture(content: str) -> str:
    """Apply all renames to a fixture YAML file."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip comments
        if stripped.startswith('#'):
            result.append(line)
            continue
        
        # contracts: -> rules: (top-level YAML key in contract blocks)
        # But NOT in description strings or envelope data
        if re.match(r'^(\s*)contracts:', line) and 'description' not in line:
            line = re.sub(r'^(\s*)contracts:', r'\1rules:', line)
        
        # kind: ContractBundle -> kind: Ruleset
        line = line.replace('kind: ContractBundle', 'kind: Ruleset')
        
        # effect: <value> -> action: <value> with value renames
        # But NOT side_effect or timeout_effect
        if re.match(r'^\s+effect:', stripped) and 'side_effect' not in line and 'timeout_effect' not in line:
            line = line.replace('effect:', 'action:')
            line = line.replace('action: deny', 'action: block')
            line = line.replace('action: approve', 'action: ask')
            # warn, redact, allow stay the same
        
        # timeout_effect value renames (key stays)
        if 'timeout_effect:' in line:
            line = line.replace('timeout_effect: deny', 'timeout_effect: block')
            # timeout_effect: allow stays
        
        # outside: value renames (key stays)  
        if re.match(r'^\s+outside:', stripped):
            line = line.replace('outside: deny', 'outside: block')
            line = line.replace('outside: "deny"', 'outside: "block"')
            line = line.replace('outside: approve', 'outside: ask')
            line = line.replace('outside: "approve"', 'outside: "ask"')
        
        # expected verdict: denied stays as "denied" (this is the expected result, not the config)
        # expected verdict values don't change - they describe what happened
        
        result.append(line)
    
    return '\n'.join(result)


def process_directory(fixtures_dir: Path, dry_run: bool = False):
    """Process all YAML fixture files."""
    changed = 0
    unchanged = 0
    errors = 0
    
    for yaml_file in sorted(fixtures_dir.rglob('*.yaml')):
        try:
            original = yaml_file.read_text()
            renamed = rename_fixture(original)
            
            if original != renamed:
                if dry_run:
                    print(f"  WOULD CHANGE: {yaml_file.relative_to(fixtures_dir)}")
                else:
                    yaml_file.write_text(renamed)
                    print(f"  CHANGED: {yaml_file.relative_to(fixtures_dir)}")
                changed += 1
            else:
                unchanged += 1
        except Exception as e:
            print(f"  ERROR: {yaml_file}: {e}")
            errors += 1
    
    print(f"\nSummary: {changed} changed, {unchanged} unchanged, {errors} errors")
    return changed, unchanged, errors


if __name__ == '__main__':
    fixtures_dir = Path(__file__).parent.parent / 'fixtures'
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("DRY RUN — no files will be modified\n")
    
    process_directory(fixtures_dir, dry_run=dry_run)
