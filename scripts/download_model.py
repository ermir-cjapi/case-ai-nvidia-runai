#!/usr/bin/env python3
"""
Model Download Script for NVIDIA Run:AI Tutorial

Downloads LLM models from HuggingFace Hub for use in the tutorial.

Usage:
    # Download Llama 3.2 3B (recommended)
    python3 download_model.py --model meta-llama/Llama-3.2-3B-Instruct --output ./model

    # Download Phi-3 Mini (alternative)
    python3 download_model.py --model microsoft/Phi-3-mini-4k-instruct --output ./model
    
    # Download with HuggingFace token
    python3 download_model.py --model meta-llama/Llama-3.2-3B-Instruct --output ./model --token YOUR_HF_TOKEN
"""

import argparse
import os
import sys
from pathlib import Path


def download_model(model_id: str, output_dir: str, token: str = None):
    """Download model from HuggingFace Hub"""
    
    try:
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer, AutoModelForCausalLM
    except ImportError:
        print("Error: Required packages not installed")
        print("\nInstall with:")
        print("  pip install transformers huggingface-hub accelerate")
        sys.exit(1)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Downloading Model: {model_id}")
    print(f"Output Directory: {output_path.absolute()}")
    print(f"{'='*60}\n")
    
    # Check if HuggingFace token is needed
    if "llama" in model_id.lower() and token is None:
        print("⚠️  Llama models require HuggingFace authentication")
        print("\nSteps:")
        print("  1. Create account: https://huggingface.co/join")
        print("  2. Accept license: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct")
        print("  3. Get token: https://huggingface.co/settings/tokens")
        print("  4. Re-run with: --token YOUR_TOKEN")
        print("\nAlternatively, use Phi-3 Mini (no token required):")
        print("  python3 download_model.py --model microsoft/Phi-3-mini-4k-instruct --output ./model")
        sys.exit(1)
    
    try:
        print("[1/3] Downloading model files...")
        print(f"  → This may take 5-15 minutes depending on connection speed")
        print(f"  → Model size: ~6-8GB\n")
        
        # Download model with snapshot_download for better progress
        cache_dir = snapshot_download(
            repo_id=model_id,
            local_dir=str(output_path),
            local_dir_use_symlinks=False,
            token=token,
            resume_download=True,
        )
        
        print(f"\n✓ Model downloaded successfully!")
        print(f"  Location: {output_path.absolute()}")
        
        # Verify model can be loaded
        print("\n[2/3] Verifying model files...")
        tokenizer = AutoTokenizer.from_pretrained(
            str(output_path),
            token=token,
            local_files_only=True
        )
        print(f"✓ Tokenizer loaded (vocab size: {len(tokenizer)})")
        
        # Just verify config without loading full model (saves time)
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(
            str(output_path),
            token=token,
            local_files_only=True
        )
        print(f"✓ Model config verified")
        print(f"  Architecture: {config.model_type}")
        print(f"  Parameters: ~{config.num_parameters // 1_000_000_000}B")
        
        print("\n[3/3] Model ready for use!")
        print(f"\nNext steps:")
        print(f"  1. cd phase1-bare-metal")
        print(f"  2. docker build -t llm-inference:phase1 .")
        print(f"  3. docker run --gpus all -p 8000:8000 -v {output_path.absolute()}:/app/model llm-inference:phase1")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error downloading model: {e}")
        
        if "401" in str(e) or "403" in str(e):
            print("\nAuthentication error. Make sure:")
            print("  1. You accepted the model license on HuggingFace")
            print("  2. Your token has read permissions")
            print("  3. Token is correct (not expired)")
        
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download LLM models for NVIDIA Run:AI tutorial",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Llama 3.2 3B (recommended, requires HF token)
  python3 download_model.py --model meta-llama/Llama-3.2-3B-Instruct --output ./model --token hf_xxx
  
  # Phi-3 Mini (alternative, no token required)
  python3 download_model.py --model microsoft/Phi-3-mini-4k-instruct --output ./model
  
  # Use HF_TOKEN environment variable
  export HF_TOKEN=hf_xxx
  python3 download_model.py --model meta-llama/Llama-3.2-3B-Instruct --output ./model
        """
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='meta-llama/Llama-3.2-3B-Instruct',
        help='HuggingFace model ID (default: meta-llama/Llama-3.2-3B-Instruct)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='./model',
        help='Output directory for model files (default: ./model)'
    )
    
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='HuggingFace access token (or set HF_TOKEN env var)'
    )
    
    args = parser.parse_args()
    
    # Check for token in environment if not provided
    token = args.token or os.getenv('HF_TOKEN')
    
    success = download_model(args.model, args.output, token)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

