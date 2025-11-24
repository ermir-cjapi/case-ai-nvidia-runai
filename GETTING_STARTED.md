# Getting Started with NVIDIA Run:AI Tutorial

## Welcome! 👋

This tutorial will teach you how to deploy LLM inference on NVIDIA GPUs with progressively better GPU utilization, culminating in **3x throughput improvement** using Run:AI.

## What You'll Learn

1. **Phase 1**: Deploy LLM inference directly on GPU (baseline)
2. **Phase 2**: Deploy to Kubernetes and discover GPU scheduling limitations
3. **Phase 3**: Use Run:AI to achieve **3x throughput on same hardware**

**Total time**: 2-3 days (can be done in stages)

## Step 0: Clone This Repository

### Option A: Using Personal Access Token (Recommended)

GitHub no longer supports password authentication. Use a Personal Access Token (PAT) instead:

1. Create a GitHub Personal Access Token:
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Select scopes: `repo` (for private repos) or just `public_repo` (for public repos)
   - Click "Generate token" and **copy the token**

2. Clone the repository:

```bash
# Replace YOUR_USERNAME with your actual GitHub username
git clone https://github.com/YOUR_USERNAME/case-ai-nvidia-runai.git
# When prompted:
# Username: your-github-username
# Password: paste-your-personal-access-token-here
```

3. (Optional) Save credentials to avoid re-entering:

```bash
git config --global credential.helper store
```

### Option B: Using SSH (Best for frequent Git users)

1. Generate SSH key (if you don't have one):

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept defaults
```

2. Add SSH key to GitHub:

```bash
# Copy your public key
cat ~/.ssh/id_ed25519.pub
# Go to https://github.com/settings/keys
# Click "New SSH key" and paste the key
```

3. Clone using SSH:

```bash
# Replace YOUR_USERNAME with your actual GitHub username
git clone git@github.com:YOUR_USERNAME/case-ai-nvidia-runai.git
```

### Option C: Download as ZIP (No Git required)

If you just want to run the tutorial without Git:

```bash
# Download and extract (replace YOUR_USERNAME with your GitHub username)
wget https://github.com/YOUR_USERNAME/case-ai-nvidia-runai/archive/refs/heads/main.zip
unzip main.zip
cd case-ai-nvidia-runai-main
```

## Prerequisites

### Required Hardware
- ✅ NVIDIA GPU with **10GB+ VRAM**
  - Examples: RTX 3080 (10GB), A10 (24GB), A100 (40GB)
  - Check: Run `nvidia-smi` on your NVIDIA server

### Required Software
1. **NVIDIA Driver** (520+)
2. **Docker** with NVIDIA Container Toolkit
3. **Kubernetes** cluster (for Phase 2 & 3)
4. **Python 3.10+**
5. **kubectl** (for Phase 2 & 3)

### Optional
- **Run:AI trial account** (for Phase 3) - https://www.run.ai/trial/
- **HuggingFace account** (free) - https://huggingface.co/join

## Step 1: Verify Your Environment

```bash
# Navigate to tutorial directory
cd case-ai-nvidia-runai

# Run environment check
python3 scripts/gpu_check.py
```

**Expected output**:
```
✓ nvidia-smi found
✓ GPU detected
  Name: NVIDIA A100-SXM4-40GB
  Memory: 40.0 GB
✓ Docker found
✓ NVIDIA Container Toolkit working
✓ kubectl found
✓ Kubernetes cluster accessible

Ready for Phase 1 (Bare Metal)
Ready for Phase 2 & 3 (Kubernetes/Run:AI)
```

If you see errors, follow the fix suggestions in the output.

## Step 2: Choose Your Model

We recommend **Llama 3.2 3B** (3 billion parameters, ~7GB VRAM).

**Option A: Llama 3.2 3B** (recommended)
- Size: ~6GB download
- License: Llama 3.2 Community License
- Requires: HuggingFace token
- Best for: Most realistic production scenario

**Option B: Phi-3 Mini** (alternative)
- Size: ~7GB download
- License: MIT (fully open)
- Requires: No token needed
- Best for: Quick start, no authentication

## Step 3: Download Model

### For Llama 3.2 3B:

1. Create HuggingFace account: https://huggingface.co/join
2. Accept license: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
3. Get token: https://huggingface.co/settings/tokens
4. Download:

```bash
export HF_TOKEN=hf_your_token_here
python3 scripts/download_model.py \
  --model meta-llama/Llama-3.2-3B-Instruct \
  --output ./model
```

### For Phi-3 Mini (no token):

```bash
python3 scripts/download_model.py \
  --model microsoft/Phi-3-mini-4k-instruct \
  --output ./model
```

**Download time**: 10-15 minutes depending on connection speed.

## Step 4: Start with Phase 1

Once the model is downloaded, you're ready!

**Option A: Using Docker Compose (Recommended)**

```bash
# Read Phase 1 guide
cat phase1-bare-metal/README.md

# Or jump right in
cd phase1-bare-metal
docker-compose up -d

# View logs
docker-compose logs -f
```

**Option B: Using Docker CLI**

```bash
cd phase1-bare-metal
docker build -t llm-inference:phase1 .
docker run --gpus all -p 8000:8000 \
  -v $(pwd)/../model:/app/model \
  llm-inference:phase1
```

**Test the service**:

```bash
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
  "generated_text": "For dry skin, I recommend starting with a gentle...",
  "tokens_generated": 142,
  "inference_time_ms": 823,
  "gpu_name": "NVIDIA A100-SXM4-40GB",
  "gpu_memory_used_gb": 6.8
}
```

## Step 5: Benchmark Phase 1

```bash
python3 scripts/load_test.py \
  --url http://localhost:8000/generate \
  --concurrency 5 \
  --requests 50
```

**Record these metrics** for comparison:
- GPU Utilization: ___% (likely ~18%)
- Throughput: ___ req/min (likely ~60)
- Latency (p50): ___ms (likely ~800ms)

## Step 6: Continue to Phase 2

Once you've completed Phase 1:

```bash
# Read Phase 2 guide
cat phase2-kubernetes/README.md

# Or follow QUICKSTART.md
cat QUICKSTART.md
```

## Step 7: Complete Phase 3

After Phase 2, tackle the exciting finale:

```bash
# Read Phase 3 guide
cat phase3-runai/README.md
```

**This is where you see the magic happen!** 🚀
- 3 pods running on 1 GPU
- 180 req/min throughput (vs 60 in Phase 2)
- 72% GPU utilization (vs 15% in Phase 2)

## Quick Reference

### File Organization

```
case-ai-nvidia-runai/
├── README.md              ← Start here for overview
├── QUICKSTART.md          ← 30-minute fast track
├── GETTING_STARTED.md     ← You are here!
├── PROJECT_SUMMARY.md     ← Final summary
│
├── scripts/
│   ├── gpu_check.py       ← Verify environment
│   ├── download_model.py  ← Download LLM
│   ├── load_test.py       ← Benchmark performance
│   └── runai_metrics.py   ← Collect Run:AI metrics
│
├── phase1-bare-metal/     ← Phase 1 files
├── phase2-kubernetes/     ← Phase 2 files
├── phase3-runai/          ← Phase 3 files
└── docs/
    └── comparison.md      ← Detailed analysis
```

### Common Commands

```bash
# Environment check
python3 scripts/gpu_check.py

# Download model
python3 scripts/download_model.py --output ./model

# Load test
python3 scripts/load_test.py --url http://localhost:8000/generate

# GPU monitoring (on NVIDIA server)
watch -n 1 nvidia-smi

# Kubernetes pods
kubectl get pods -w

# Run:AI workloads
runai list
```

## Troubleshooting

### "Password authentication not supported" (Git)
**Solution**: GitHub requires Personal Access Token or SSH key.
- See detailed guide: [docs/git-authentication.md](docs/git-authentication.md)
- Quick fix: Use PAT instead of password: https://github.com/settings/tokens

### "CUDA out of memory"
**Solution**: Your GPU has less than 10GB VRAM.
- Use Phi-3 Mini instead of Llama 3.2 3B
- Or reduce batch size in requests

### "nvidia-smi not found"
**Solution**: NVIDIA drivers not installed.
- Install from: https://www.nvidia.com/download/index.aspx
- Reboot after installation

### "Docker NVIDIA runtime not working"
**Solution**: NVIDIA Container Toolkit not installed.
- Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
- Verify: `docker run --rm --gpus all nvidia/cuda:12.2.0-base nvidia-smi`

### "Model download fails"
**Solution**: HuggingFace authentication issue (for Llama models).
- Ensure you accepted the license
- Check token has read permissions
- Try Phi-3 Mini (no token required)

### "Kubernetes cluster not accessible"
**Solution**: kubectl not configured.
- For Phase 1 only: Skip K8s, just use Docker
- For Phase 2 & 3: Install K3s, minikube, or configure existing cluster

## Learning Path Recommendations

### Beginner
1. **Phase 1 only** (1 day)
   - Learn GPU inference basics
   - Understand model loading and memory
   - Skip K8s complexity

### Intermediate
1. **Phase 1** (4 hours)
2. **Phase 2** (5 hours)
   - Learn K8s GPU scheduling
   - Understand limitations

### Advanced
1. **All 3 phases** (2-3 days)
   - Complete tutorial
   - Compare all approaches
   - Production-ready knowledge

## Expected Results Summary

| Phase | Time | GPU Util | Throughput | Difficulty |
|-------|------|----------|------------|------------|
| **1** | 4h | 18% | 60 req/min | ⭐ Easy |
| **2** | 5h | 15% | 60 req/min | ⭐⭐⭐ Medium |
| **3** | 4h | **72%** | **180 req/min** | ⭐⭐⭐⭐ Hard |

**Key insight**: Phase 3 achieves **3x throughput** with **4.8x better GPU utilization**!

## Next Steps

1. ✅ Verify environment: `python3 scripts/gpu_check.py`
2. ✅ Download model: `python3 scripts/download_model.py`
3. ✅ Start Phase 1: `cd phase1-bare-metal && cat README.md`
4. ✅ Benchmark each phase
5. ✅ Compare results in `docs/comparison.md`

## Need Help?

- **Documentation**: Each phase has detailed README.md
- **Quick answers**: See QUICKSTART.md
- **Analysis**: See docs/comparison.md
- **Issues**: Check logs (`docker logs` or `kubectl logs`)

## Have Fun! 🚀

This tutorial represents real-world production scenarios. Completing it will give you:
- Deep understanding of GPU inference deployment
- Hands-on Kubernetes GPU scheduling experience
- Production-ready Run:AI knowledge
- **Proof of 67% cost savings** for GPU workloads

**Ready? Let's go!**

```bash
python3 scripts/gpu_check.py
```

