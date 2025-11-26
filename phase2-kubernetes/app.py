"""
FastAPI LLM Inference Server - Phase 2: Kubernetes
Same code as Phase 1, deployed to Kubernetes with GPU scheduling
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncIterator
from contextlib import asynccontextmanager
import torch
from model_loader import ModelLoader
import logging
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model loader (initialized on startup)
model_loader: Optional[ModelLoader] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    global model_loader
    
    # Startup
    logger.info("Starting LLM Inference Server...")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        logger.warning("No GPU detected! This will be very slow.")
    
    try:
        model_loader = ModelLoader(model_path="/app/model")
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    yield
    
    # Shutdown
    if model_loader:
        del model_loader
        torch.cuda.empty_cache()
    logger.info("Server shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="LLM Inference API",
    description="GPU-accelerated text generation with Llama 3.2 3B",
    version="1.0.0",
    lifespan=lifespan
)


class GenerateRequest(BaseModel):
    """Request schema for text generation"""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Input prompt for generation")
    max_tokens: int = Field(default=200, ge=1, le=1000, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.1, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling threshold")
    stream: bool = Field(default=False, description="Enable streaming response")


class GenerateResponse(BaseModel):
    """Response schema for text generation"""
    generated_text: str
    prompt: str
    tokens_generated: int
    inference_time_ms: float
    gpu_name: str
    gpu_memory_used_gb: float


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_loader is not None,
        "gpu_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    if not model_loader:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    gpu_stats = {}
    if torch.cuda.is_available():
        gpu_stats = {
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_memory_allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
            "gpu_memory_reserved_gb": torch.cuda.memory_reserved(0) / 1024**3,
            "gpu_memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
        }
    
    return {
        "status": "healthy",
        "model_loaded": True,
        **gpu_stats
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text from prompt"""
    
    if not model_loader:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        start_time = time.time()
        
        # Generate text
        generated_text = model_loader.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        end_time = time.time()
        inference_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Get GPU stats
        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        gpu_memory_gb = torch.cuda.memory_allocated(0) / 1024**3 if torch.cuda.is_available() else 0
        
        # Count tokens (approximate)
        tokens_generated = len(generated_text.split())
        
        logger.info(f"Generated {tokens_generated} tokens in {inference_time:.0f}ms")
        
        return GenerateResponse(
            generated_text=generated_text,
            prompt=request.prompt,
            tokens_generated=tokens_generated,
            inference_time_ms=inference_time,
            gpu_name=gpu_name,
            gpu_memory_used_gb=gpu_memory_gb
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/generate-stream")
async def generate_stream(request: GenerateRequest):
    """Generate text with streaming response (future enhancement)"""
    
    if not model_loader:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # For now, return non-streaming response
    # Streaming implementation would require TextIteratorStreamer from transformers
    return await generate(request)


@app.get("/stats")
async def stats():
    """Get GPU statistics"""
    
    if not torch.cuda.is_available():
        return {"error": "No GPU available"}
    
    return {
        "gpu_name": torch.cuda.get_device_name(0),
        "gpu_count": torch.cuda.device_count(),
        "cuda_version": torch.version.cuda,
        "pytorch_version": torch.__version__,
        "memory": {
            "allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
            "reserved_gb": torch.cuda.memory_reserved(0) / 1024**3,
            "total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            "free_gb": (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
