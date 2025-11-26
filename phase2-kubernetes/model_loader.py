"""
Model Loader for LLM Inference - Phase 2: Kubernetes
Same code as Phase 1
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaTokenizerFast
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelLoader:
    """Load and manage LLM on GPU"""
    
    def __init__(self, model_path: str = "/app/model", device: str = "auto"):
        """
        Initialize model loader
        
        Args:
            model_path: Path to model directory
            device: Device to load model on ('auto', 'cuda', 'cpu')
        """
        self.model_path = model_path
        self.device = self._get_device(device)
        
        logger.info(f"Loading model from {model_path}")
        logger.info(f"Target device: {self.device}")
        
        # Load tokenizer - use specific tokenizer class to avoid AutoTokenizer bug
        try:            
            # Try to load as LlamaTokenizerFast first (for Llama 3.2)
            try:
                self.tokenizer = LlamaTokenizerFast.from_pretrained(
                    model_path,
                    legacy=False
                )
                logger.info("Loaded LlamaTokenizerFast")
            except Exception as e:
                logger.warning(f"Failed to load LlamaTokenizerFast: {e}")
                # Fallback to AutoTokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=True
                )
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            logger.error("This usually means the model files are corrupted or incomplete.")
            logger.error(f"Please check that {model_path} contains valid model files.")
            logger.error("Try re-downloading the model with: python3 scripts/download_model.py")
            raise
        
        # Set padding token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model with optimizations
        logger.info("Loading model to GPU...")
        if self.device == "cuda":
            # Force model to GPU (don't let accelerate offload to CPU)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="cuda:0",  # Force all layers to GPU 0
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
        else:
            # CPU mode
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            self.model = self.model.to(self.device)
        
        # Set to evaluation mode
        self.model.eval()
        
        # Log model info
        self._log_model_info()
        
        logger.info("Model loaded successfully!")
    
    def _get_device(self, device: str) -> str:
        """Determine device to use"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _log_model_info(self):
        """Log model and GPU information"""
        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Model parameters: {total_params / 1e9:.2f}B")
        
        # GPU memory if available
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            reserved = torch.cuda.memory_reserved(0) / 1024**3
            logger.info(f"GPU memory allocated: {allocated:.2f} GB")
            logger.info(f"GPU memory reserved: {reserved:.2f} GB")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        do_sample: bool = True
    ) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter
            do_sample: Whether to use sampling (vs greedy decoding)
        
        Returns:
            Generated text (without prompt)
        """
        # Tokenize input
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                use_cache=True,  # Enable KV cache for faster generation
            )
        
        # Decode output
        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        # Remove prompt from output
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()
        
        return generated_text
    
    def __del__(self):
        """Cleanup GPU memory on deletion"""
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
