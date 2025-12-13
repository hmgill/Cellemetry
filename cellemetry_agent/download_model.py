#!/usr/bin/env python3
"""Download and verify SAM3 model cache."""

from transformers import Sam3Model, Sam3Processor
import os
from pathlib import Path

print(f"HF_HOME: {os.environ.get('HF_HOME')}")

# Download model
print("Downloading SAM3 model...")
model = Sam3Model.from_pretrained('facebook/sam3')
processor = Sam3Processor.from_pretrained('facebook/sam3')
print('✅ SAM3 model downloaded successfully!')

# Verify cache location
cache_dir = Path(os.environ.get('HF_HOME', '/root/.cache/huggingface'))
print(f'Cache directory: {cache_dir}')

if cache_dir.exists():
    for root, dirs, files in os.walk(cache_dir):
        if 'sam3' in root.lower():
            print(f'Found SAM3 in: {root}')
            break
