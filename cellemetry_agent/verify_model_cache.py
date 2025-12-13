#!/usr/bin/env python3
"""Verify SAM3 model cache location."""

from pathlib import Path
import os

hf_home = Path(os.environ.get('HF_HOME', '/app/models'))
print(f'Checking HF_HOME: {hf_home}')

possible_paths = [
    hf_home / 'models--facebook--sam3',
    hf_home / 'hub' / 'models--facebook--sam3'
]

found = False
for p in possible_paths:
    if p.exists():
        print(f'✅ Found model cache at: {p}')
        found = True
        # List contents
        for item in os.listdir(p):
            print(f'  - {item}')
        break

if not found:
    print('⚠️  Model cache not found in expected locations')
    print('Listing /app/models contents:')
    for root, dirs, files in os.walk('/app/models'):
        print(f'{root}:')
        for d in dirs[:5]:
            print(f'  [DIR] {d}')
        for f in files[:5]:
            print(f'  [FILE] {f}')
        if len(dirs) > 5 or len(files) > 5:
            print('  ...')
        break
