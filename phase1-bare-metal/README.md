# Phase 1: Bare Metal GPU Inference

This phase demonstrates direct GPU inference without any orchestration frameworks. You'll run the LLM inference server directly on your NVIDIA GPU using Docker.

## 🎯 Learning Objectives

- Load and run LLM models directly on GPU
- Understand GPU memory management (model weights + KV cache)
- Measure baseline performance (latency, throughput, GPU utilization)
- Identify GPU idle time and resource waste

## 📋 Prerequisites

Before starting, ensure you have:

1. ✅ NVIDIA GPU with 10GB+ VRAM
2. ✅ NVIDIA drivers installed (520+)
3. ✅ Docker with NVIDIA Container Toolkit
4. ✅ Model downloaded to `../model/` directory

### Verify Prerequisites

```bash
# Check GPU
nvidia-smi

# Check Docker NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Verify model exists
ls -lh ../model/
```

## 🚀 Quick Start

### Step 1: Build Docker Image

```bash
cd phase1-bare-metal
docker build -t llm-inference:phase1 .
```

**Build time**: ~5-10 minutes (downloads PyTorch, Transformers, etc.)

### Step 2: Run Inference Server

```bash
# Run with GPU and model mounted
docker run --rm --gpus all \
  -p 8000:8000 \
  -v $(pwd)/../model:/app/model \
  llm-inference:phase1
```

**Startup time**: ~30-60 seconds (model loading to GPU)

You should see:
```
INFO: Loading model from /app/model
INFO: GPU: NVIDIA A100-SXM4-40GB
INFO: Model loaded successfully!
INFO: Application startup complete.
```

### Step 3: Test Inference

Open a new terminal:

```bash
# Simple test
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Suggest a skincare routine for dry skin",
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

**Expected response** (example):
```json
{
  "generated_text": "For dry skin, I recommend starting with a gentle cleanser...",
  "prompt": "Suggest a skincare routine for dry skin",
  "tokens_generated": 145,
  "inference_time_ms": 823.4,
  "gpu_name": "NVIDIA A100-SXM4-40GB",
  "gpu_memory_used_gb": 6.8
}
```

### Step 4: Check GPU Utilization

While the server is running, monitor GPU in another terminal:

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi
```

**Observe**:
- GPU memory usage: ~7-8GB (model weights + KV cache)
- GPU utilization: **Spikes to 90-100% during inference, then drops to 0%**
- **Key insight**: GPU is idle most of the time between requests!

### Step 5: Run Load Test

```bash
cd ..
python scripts/load_test.py \
  --url http://localhost:8000/generate \
  --concurrency 5 \
  --requests 50
```

**Expected output**:
```
LOAD TEST RESULTS
==========================================================

Success Rate:
  Total requests: 50
  Successful: 50
  Success rate: 100.0%

Latency (ms):
  Min: 720
  Max: 1543
  Mean: 856
  Median (p50): 831
  p95: 1021
  p99: 1234

Throughput:
  Total time: 42.3s
  Requests/sec: 1.18
  Requests/min: 71
```

## 📊 Key Metrics to Record

Record these metrics for comparison with Phase 2 and Phase 3:

| Metric | Your Value | Expected Range |
|--------|------------|----------------|
| **Model Load Time** | ___ sec | 30-60 sec |
| **GPU Memory Used** | ___ GB | 6-8 GB |
| **Latency (p50)** | ___ ms | 700-1000 ms |
| **Latency (p95)** | ___ ms | 1000-1500 ms |
| **Throughput** | ___ req/min | 60-90 req/min |
| **GPU Utilization (avg)** | ___ % | **15-25%** |
| **GPU Idle Time** | ___ % | **75-85%** |

### How to Measure GPU Utilization

While running load test:

```bash
# In separate terminal
nvidia-smi dmon -s u -c 60
```

Average the GPU utilization column. You'll likely see:
- **Peak**: 90-100% (during active inference)
- **Average**: 15-25% (due to idle time between requests)

## 🔍 Analysis

### What You Should Observe

1. **High GPU Idle Time**: 
   - GPU utilization spikes during inference (90-100%)
   - Then drops to 0% between requests
   - Average utilization: only 15-25%

2. **Memory Always Occupied**:
   - Model occupies ~7GB VRAM constantly
   - Memory not freed between requests
   - GPU memory "reserved" but not actively used

3. **Performance Characteristics**:
   - Inference latency: 700-1000ms per request
   - Throughput limited by sequential processing
   - No queueing or batching optimizations

### Key Insights

❌ **Problems Identified**:
- GPU is idle 75-85% of the time
- Can only serve 1 request at a time
- GPU memory occupied but underutilized
- Manual deployment and monitoring required

✅ **What Works Well**:
- Direct GPU control (no overhead)
- Predictable performance
- Simple to understand and debug

## 📝 Exercises

### Exercise 1: Measure Peak Performance

Send requests as fast as possible:

```bash
python scripts/load_test.py --concurrency 10 --requests 100
```

**Question**: Does throughput increase? Why or why not?

### Exercise 2: Monitor GPU Memory

```bash
# Watch memory usage
watch -n 0.5 'nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv'
```

**Question**: How much memory is actually used during inference vs idle?

### Exercise 3: Vary Request Concurrency

Try different concurrency levels:

```bash
# Test 1: Sequential (concurrency=1)
python scripts/load_test.py --concurrency 1 --requests 20

# Test 2: Moderate (concurrency=5)
python scripts/load_test.py --concurrency 5 --requests 20

# Test 3: High (concurrency=10)
python scripts/load_test.py --concurrency 10 --requests 20
```

**Question**: How does latency change with concurrency? Why?

## 🛠️ Troubleshooting

### "CUDA out of memory" Error

**Solution**: Your GPU has less than 10GB VRAM. Options:
1. Use Phi-3 Mini with INT8 quantization
2. Enable gradient checkpointing (reduces memory)
3. Use a smaller model

### Slow Startup (>2 minutes)

**Cause**: Model downloading from cache or CPU inference

**Solution**: Verify model is in correct location:
```bash
ls -lh ../model/
# Should show config.json, model files, etc.
```

### Low Throughput (<30 req/min)

**Possible causes**:
1. CPU inference (no GPU detected)
2. Network latency in load test
3. Model too large for GPU

**Check GPU usage**:
```bash
docker logs <container_id> | grep GPU
# Should show: "GPU: NVIDIA ..."
```

## 📚 Additional Resources

### API Endpoints

- `GET /` - Health check (basic)
- `GET /health` - Detailed health with GPU stats
- `POST /generate` - Text generation
- `GET /stats` - Current GPU statistics

### Example: Check GPU Stats

```bash
curl http://localhost:8000/stats | jq
```

Response:
```json
{
  "gpu_name": "NVIDIA A100-SXM4-40GB",
  "gpu_count": 1,
  "cuda_version": "12.2",
  "pytorch_version": "2.1.0",
  "memory": {
    "allocated_gb": 6.8,
    "reserved_gb": 7.2,
    "total_gb": 40.0,
    "free_gb": 33.2
  }
}
```

## ✅ Phase 1 Complete!

You should now understand:
- ✅ How to load LLMs to GPU
- ✅ GPU memory requirements for inference
- ✅ Baseline performance characteristics
- ✅ **GPU idle time problem** (75-85% idle!)

### Key Takeaway

**The GPU is idle 75-85% of the time**, wasting expensive compute resources. In Phase 2, we'll deploy to Kubernetes to enable scaling, but you'll discover that doesn't solve the idle GPU problem!

## Next Steps

Continue to **[Phase 2: Kubernetes](../phase2-kubernetes/README.md)** to:
- Deploy inference service to Kubernetes
- Use NVIDIA GPU Operator for GPU scheduling
- Attempt to scale (and discover K8s GPU limitations!)
- Compare performance and GPU utilization

