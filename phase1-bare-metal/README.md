# Phase 1: Bare Metal GPU Inference

Run LLM inference directly on your NVIDIA GPU using Docker. This is your baseline - simple, fast, but inefficient.

## ⏱️ Quick Overview

| 🎯 Goal | ⏱️ Time | 📊 Difficulty |
|---------|---------|---------------|
| Deploy LLM on GPU, measure baseline performance | 30 minutes | ⭐ Easy |

**What you'll discover**: Your expensive GPU is idle 75-85% of the time! 😱

## 🎯 What You'll Learn

- ✅ How to load and run LLMs directly on GPU
- ✅ GPU memory requirements (model weights + KV cache)
- ✅ Baseline performance metrics (latency, throughput)
- ✅ **The GPU idle time problem** (GPUs are idle most of the time!)
- ✅ Why this wastes money in production

## 🚀 Quick Start (TL;DR)

> **💡 Tip**: Print the [CHEATSHEET.md](CHEATSHEET.md) for a one-page reference!

**Already have model downloaded?** Just run these 4 commands:

```bash
# 1️⃣ Start the server (from project root)
cd phase1-bare-metal && docker-compose up -d

# 2️⃣ Test it works
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine", "max_tokens": 150}'

# 3️⃣ Benchmark performance
cd .. && python3 scripts/load_test.py --url http://localhost:8000/generate --concurrency 5

# 4️⃣ Monitor GPU (open new terminal)
watch -n 1 nvidia-smi
```

**That's it!** You'll see the GPU idle time problem in action.

<details>
<summary>📖 Need detailed step-by-step instructions? Click here</summary>

Full detailed walkthrough below with explanations, troubleshooting, and learning exercises. ⬇️

</details>

---

## 📋 Before You Start

Make sure you have:

1. ✅ **NVIDIA GPU** with 10GB+ VRAM
2. ✅ **NVIDIA drivers** installed (520+)
3. ✅ **Docker** with NVIDIA Container Toolkit
4. ✅ **Model downloaded** to `../model/` directory (use `scripts/download_model.py`)

### Quick Verification

```bash
# 1. Check GPU
nvidia-smi

# 2. Check Docker NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# 3. Verify model exists
ls -lh ../model/
# You should see: config.json, tokenizer files, model weights, etc.
```

## 🚀 Running Phase 1

### Step 1: Start the Inference Server

Choose either Docker Compose (easier) or Docker CLI:

**Option A: Docker Compose (Recommended - Easiest)**

```bash
cd phase1-bare-metal

# Start the service (builds automatically if needed)
docker-compose up -d

# View logs to confirm it's running
docker-compose logs -f
```

**Option B: Docker CLI (Manual Control)**

```bash
cd phase1-bare-metal

# Build the Docker image
docker build -t llm-inference:phase1 .

# Run the container
docker run --rm --gpus all \
  -p 8000:8000 \
  -v $(pwd)/../model:/app/model \
  llm-inference:phase1
```

**⏱️ Expected Times:**
- **First build**: 5-10 minutes (downloads PyTorch, Transformers, etc.)
- **Startup**: 30-60 seconds (loading model to GPU)

### Step 2: Verify It's Running

Look for these log messages:

```
INFO: Loading model from /app/model
INFO: GPU: NVIDIA A100-SXM4-40GB (or your GPU name)
INFO: Model loaded successfully!
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

✅ **Success!** Your LLM is now running on GPU and ready for inference.

### Step 3: Test Your First Inference

Open a **new terminal** window and try this:

```bash
# Simple health check first
curl http://localhost:8000/

# Now test text generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Suggest a skincare routine for dry skin",
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

**What You Should See:**

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

🎉 **It works!** You just ran your first GPU-accelerated LLM inference!

### Step 4: Monitor GPU Performance

Open **another terminal** and watch the GPU in real-time:

```bash
# Real-time GPU monitoring (updates every 1 second)
watch -n 1 nvidia-smi
```

**What to Look For:**
- 📊 **GPU Memory**: ~7-8GB occupied (model weights + KV cache)
- ⚡ **GPU Utilization**: Spikes to 90-100% during inference
- 😴 **Idle Time**: Drops to 0% between requests

**💡 Key Insight**: The GPU is idle 75-85% of the time! This is the problem we'll solve in Phase 3.

### Step 5: Run Performance Benchmark

Back in your project root, run a load test to measure baseline performance:

```bash
cd ..  # Go back to project root
python3 scripts/load_test.py \
  --url http://localhost:8000/generate \
  --concurrency 5 \
  --requests 50
```

**Expected Results:**

```
============================================================
LOAD TEST RESULTS
============================================================

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
============================================================
```

## 📊 Record Your Baseline Metrics

**Write down these numbers** - you'll compare them with Phase 2 and Phase 3!

| Metric | Your Value | Expected Range |
|--------|------------|----------------|
| **Model Load Time** | _______ sec | 30-60 sec |
| **GPU Memory Used** | _______ GB | 6-8 GB |
| **Latency (p50)** | _______ ms | 700-1000 ms |
| **Latency (p95)** | _______ ms | 1000-1500 ms |
| **Throughput** | _______ req/min | 60-90 req/min |
| **GPU Utilization (avg)** | _______ % | **15-25%** ⚠️ |
| **GPU Idle Time** | _______ % | **75-85%** ⚠️ |

### How to Measure Average GPU Utilization

Run this while the load test is running:

```bash
# Monitor GPU utilization for 60 seconds
nvidia-smi dmon -s u -c 60
```

You'll see:
- **Peak**: 90-100% (when actively generating text)
- **Average**: 15-25% (because GPU is idle between requests)

**This low average utilization is what we'll improve in Phase 3!**

## 🔍 Understanding What You Just Saw

### Visual: What's Happening on Your GPU

```
Time →  [0s]    [1s]    [2s]    [3s]    [4s]    [5s]    [6s]
        ┌───────────────────────────────────────────────────┐
GPU:    │ 95% │ 5%  │ 5%  │ 95% │ 5%  │ 5%  │ 5%  │ ...  │
        └───────────────────────────────────────────────────┘
         ▲                   ▲
      Request 1          Request 2
      (1 second)         (1 second)
      
      ⚠️ Average GPU Utilization: ~18%
      💰 Waste: 82% of GPU time is IDLE
```

**The Pattern**: 
- Request arrives → GPU spikes to 95% for ~1 second
- Request completes → GPU drops to 5% (idle)
- Wait for next request → GPU still idle...
- Next request → Spike again

### The Good News ✅

1. **It Works!**
   - Model loads successfully to GPU
   - Inference is fast (700-1000ms per request)
   - Predictable, stable performance
   - Simple to deploy and debug

2. **Peak Performance is Great**
   - GPU hits 90-100% utilization during inference
   - CUDA acceleration is working
   - Model fits in GPU memory

### The Problem ❌

1. **Massive GPU Idle Time**
   - GPU utilization: **only 15-25% on average**
   - GPU sits idle **75-85% of the time**
   - You're paying for a GPU that's mostly doing nothing!

2. **Memory is Locked**
   - ~7GB VRAM occupied 24/7
   - Memory not freed between requests
   - Can't run other workloads on the same GPU

3. **Limited Scalability**
   - Only 1 pod per GPU
   - Can't handle traffic spikes efficiently
   - Manual scaling and deployment

### Why This Matters 💰

If you're using a cloud GPU instance:
- **AWS p3.2xlarge (V100)**: ~$3/hour
- **Average GPU utilization**: 18%
- **Effective cost**: $16.67/hour of actual compute
- **Waste**: ~$2.50/hour sitting idle

**Phase 3 will fix this with Run:AI GPU sharing!**

## 🎓 Optional: Experiment and Learn

### Experiment 1: Test Higher Concurrency

What happens when you send more requests simultaneously?

```bash
python3 scripts/load_test.py --concurrency 10 --requests 100
```

**💭 Think About It**: Did throughput increase? Why or why not?

<details>
<summary>Click to see the answer</summary>

**Answer**: Throughput stays roughly the same! The model can only process one request at a time. Extra concurrent requests just queue up waiting. This is a fundamental limitation we'll address in Phase 3.

</details>

### Experiment 2: Watch GPU Memory Patterns

```bash
# Watch memory usage with detailed stats
watch -n 0.5 'nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv'
```

**💭 Think About It**: Does memory usage change during inference vs idle?

<details>
<summary>Click to see the answer</summary>

**Answer**: Memory stays constant! The model is always loaded (~7GB). Only a tiny amount of extra memory is used during active inference for the KV cache.

</details>

### Experiment 3: Compare Different Concurrency Levels

```bash
# Sequential (one at a time)
python3 scripts/load_test.py --concurrency 1 --requests 20

# Moderate (5 at once)
python3 scripts/load_test.py --concurrency 5 --requests 20

# High (10 at once)
python3 scripts/load_test.py --concurrency 10 --requests 20
```

**💭 Think About It**: How does latency change with concurrency?

<details>
<summary>Click to see the answer</summary>

**Answer**: Higher concurrency = higher latency! With concurrency=10, each request waits for 9 others to complete first. But total throughput (req/min) stays the same because the GPU can only process one at a time.

</details>

## 🔧 Useful Commands Reference

### Docker Compose Commands

```bash
# Start service (detached/background mode)
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop service
docker-compose down

# Restart service
docker-compose restart

# Execute commands inside container
docker-compose exec llm-inference nvidia-smi
docker-compose exec llm-inference bash

# Rebuild from scratch
docker-compose down
docker-compose up --build
```

### API Endpoints

```bash
# Health check (simple)
curl http://localhost:8000/

# Health check (detailed with GPU stats)
curl http://localhost:8000/health

# Generate text
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your prompt here", "max_tokens": 200}'

# Get GPU statistics
curl http://localhost:8000/stats | jq
```

### GPU Monitoring

```bash
# Basic GPU check
nvidia-smi

# Real-time monitoring
watch -n 1 nvidia-smi

# Utilization monitoring (for benchmarking)
nvidia-smi dmon -s u -c 60

# Detailed memory stats
nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv
```

## 🛠️ Troubleshooting

### Issue: "Could not select device driver with capabilities: [[gpu]]"

This means Docker can't access the GPU.

**Solution**:
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Test it
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### Issue: "CUDA out of memory"

Your GPU doesn't have enough VRAM (needs 10GB+).

**Solution**: Use a smaller model or quantization:
```bash
# Download Phi-3 Mini instead (smaller footprint)
python3 scripts/download_model.py \
  --model microsoft/Phi-3-mini-4k-instruct \
  --output ./model
```

### Issue: Slow Startup (>2 minutes)

**Check**: Is the model in the right place?

```bash
ls -lh ../model/
# You should see: config.json, tokenizer.json, model files, etc.
```

**If model is missing**: Download it first!
```bash
cd ..
python3 scripts/download_model.py \
  --model meta-llama/Llama-3.2-3B-Instruct \
  --output ./model \
  --token YOUR_HF_TOKEN
```

### Issue: "Model not loaded" Error (503)

The container started but the model didn't load.

**Debug steps**:
```bash
# Check the logs
docker-compose logs

# Common causes:
# 1. Model directory is empty or wrong path
# 2. Model files are corrupted
# 3. Not enough GPU memory
```

### Issue: Container Keeps Restarting

```bash
# View the error logs
docker-compose logs --tail=50

# Common causes:
# 1. GPU not accessible
# 2. CUDA version mismatch
# 3. Out of memory
```

### Issue: Low Throughput (<30 req/min)

**Check if GPU is being used**:
```bash
# View logs for GPU detection
docker-compose logs | grep GPU

# Should show: "GPU: NVIDIA [Your GPU Name]"
# If it says "No GPU detected", GPU isn't accessible
```

**Check GPU during inference**:
```bash
watch -n 1 nvidia-smi
# GPU utilization should spike to 90-100% during requests
```

## ✅ Phase 1 Complete! What You Learned

Congratulations! You've successfully:

- ✅ Deployed an LLM inference server with GPU acceleration
- ✅ Measured baseline performance metrics
- ✅ Discovered the **GPU idle time problem** (75-85% idle!)
- ✅ Understood GPU memory requirements (~7GB for this model)

### 🔑 Key Takeaway

**Your GPU is idle 75-85% of the time**, wasting expensive compute resources!

Even though:
- Peak performance is great (90-100% during inference)
- Latency is good (700-1000ms per request)
- The system works perfectly

**The problem**: Between requests, the GPU sits idle while still occupying memory and costing money.

### 💡 What's Next?

In **Phase 2**, you'll deploy to Kubernetes and try to scale... but you'll discover that **Kubernetes can't solve this problem** either! Traditional K8s treats GPUs as indivisible resources.

Finally, in **Phase 3**, you'll use **Run:AI** to achieve:
- ✨ **3x throughput** on the same hardware
- ✨ **60-80% GPU utilization** (vs 15-25% now)
- ✨ **Multiple pods sharing one GPU**
- ✨ **67% cost savings**

---

## 📚 Quick Reference

### All API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Simple health check |
| `/health` | GET | Detailed health + GPU stats |
| `/generate` | POST | Generate text from prompt |
| `/stats` | GET | Current GPU statistics |

### Example: Get GPU Stats

```bash
curl http://localhost:8000/stats | jq
```

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

---

## 🚀 Continue to Phase 2

Ready to deploy to Kubernetes?

```bash
# Read the Phase 2 guide
cd ../phase2-kubernetes
cat README.md

# Or jump straight to the main README
cd ..
cat README.md
```

**Phase 2** will show you:
- How to deploy LLM inference on Kubernetes
- NVIDIA GPU Operator for GPU resource management
- Why traditional K8s can't solve the GPU utilization problem
- The limitations that Run:AI overcomes

**See you in Phase 2!** 🎯

