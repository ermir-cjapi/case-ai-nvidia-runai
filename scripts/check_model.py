#!/usr/bin/env python3
"""
Check if model directory is valid and complete
"""

import json
import os
import sys
from pathlib import Path

def check_model_directory(model_path: str):
    """Check if model directory has all required files"""
    
    model_dir = Path(model_path)
    
    if not model_dir.exists():
        print(f"❌ Model directory does not exist: {model_path}")
        return False
    
    print(f"📁 Checking model directory: {model_path}")
    print()
    
    # Required files
    required_files = {
        'config.json': 'Model configuration',
        'tokenizer.json': 'Tokenizer',
        'tokenizer_config.json': 'Tokenizer configuration',
    }
    
    # Check for model weight files (various formats)
    model_files = list(model_dir.glob('*.safetensors')) + \
                  list(model_dir.glob('*.bin')) + \
                  list(model_dir.glob('*.pth')) + \
                  list(model_dir.glob('*.pt'))
    
    all_good = True
    
    # Check required files
    for filename, description in required_files.items():
        filepath = model_dir / filename
        if filepath.exists():
            print(f"✓ {description}: {filename}")
            
            # Validate JSON files
            if filename.endswith('.json'):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    if filename == 'config.json':
                        # Check if it's a proper config
                        if isinstance(data, dict) and 'model_type' in data:
                            print(f"  Model type: {data['model_type']}")
                        else:
                            print(f"  ⚠️  WARNING: config.json is missing 'model_type' field")
                            print(f"  This is likely the cause of your error!")
                            all_good = False
                            
                except json.JSONDecodeError as e:
                    print(f"  ❌ ERROR: Invalid JSON in {filename}: {e}")
                    all_good = False
        else:
            print(f"❌ Missing {description}: {filename}")
            all_good = False
    
    # Check model weights
    if model_files:
        print(f"✓ Model weights found: {len(model_files)} file(s)")
        total_size = sum(f.stat().st_size for f in model_files) / (1024**3)
        print(f"  Total size: {total_size:.2f} GB")
        for f in model_files[:3]:  # Show first 3
            size = f.stat().st_size / (1024**3)
            print(f"  - {f.name} ({size:.2f} GB)")
        if len(model_files) > 3:
            print(f"  ... and {len(model_files) - 3} more")
    else:
        print(f"❌ No model weight files found (.safetensors, .bin, .pth, .pt)")
        all_good = False
    
    print()
    
    # List all files in directory
    all_files = sorted([f.name for f in model_dir.iterdir() if f.is_file()])
    print(f"📋 All files in directory ({len(all_files)}):")
    for filename in all_files[:20]:  # Show first 20
        print(f"  - {filename}")
    if len(all_files) > 20:
        print(f"  ... and {len(all_files) - 20} more")
    
    print()
    
    if all_good:
        print("✅ Model directory appears to be complete and valid!")
        return True
    else:
        print("❌ Model directory has issues. Please re-download the model:")
        print()
        print("  python3 scripts/download_model.py \\")
        print("    --model meta-llama/Llama-3.2-3B-Instruct \\")
        print("    --output ./model \\")
        print("    --token YOUR_HF_TOKEN")
        print()
        return False


if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else "./model"
    
    print("=" * 60)
    print("Model Directory Validation")
    print("=" * 60)
    print()
    
    result = check_model_directory(model_path)
    sys.exit(0 if result else 1)

