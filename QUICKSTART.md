# Quick Start Guide - NVIDIA Run:AI Tutorial

Get up and running with the tutorial in 30 minutes or less!

## Step 0: Clone Repository

⚠️ **GitHub Authentication Note**: Password authentication is not supported. Use one of these methods:

```bash
# Method 1: HTTPS with Personal Access Token (replace YOUR_USERNAME with your GitHub username)
git clone https://github.com/YOUR_USERNAME/case-ai-nvidia-runai.git
# Use your PAT (not password) when prompted: https://github.com/settings/tokens

# Method 2: SSH (replace YOUR_USERNAME with your GitHub username)
git clone git@github.com:YOUR_USERNAME/case-ai-nvidia-runai.git

# Method 3: Download ZIP (no Git) - replace YOUR_USERNAME with your GitHub username
wget https://github.com/YOUR_USERNAME/case-ai-nvidia-runai/archive/refs/heads/main.zip && unzip main.zip
```

Then navigate to the directory:

```bash
cd case-ai-nvidia-runai
```

## Prerequisites Check

Run this command to verify your environment:

```bash
python3 scripts/gpu_check.py
```

Expected output:
- ✅ nvidia-smi found
- ✅ GPU detected (10GB+ VRAM)
- ✅ Docker found
- ✅ NVIDIA Container Toolkit working

## 5-Minute Phase 1 (Bare Metal)

### Step 1: Download Model

```bash
# For Llama 3.2 3B (requires HuggingFace token)
export HF_TOKEN=your_token_here
python3 scripts/download_model.py --model meta-llama/Llama-3.2-3B-Instruct --output ./model

# OR use Phi-3 Mini (no token required)
python3 scripts/download_model.py --model microsoft/Phi-3-mini-4k-instruct --output ./model
```

### Step 2: Run Inference Server

**Option A: Docker Compose (Easiest)**
```bash
cd phase1-bare-metal
docker-compose up -d
```

**Option B: Docker CLI**
```bash
cd phase1-bare-metal
docker build -t llm-inference:phase1 .
docker run --gpus all -p 8000:8000 -v $(pwd)/../model:/app/model llm-inference:phase1
```

### Step 3: Test

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine", "max_tokens": 100}'
```

### Step 4: Benchmark

```bash
python3 scripts/load_test.py --url http://localhost:8000/generate --concurrency 5 --requests 50
```

**Record these metrics** for comparison!

## 20-Minute Phase 2 (Kubernetes)

### Step 1: Install GPU Operator

```bash
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia && helm repo update
helm install --wait --generate-name -n gpu-operator --create-namespace nvidia/gpu-operator
```

### Step 2: Deploy to K8s

```bash
cd ../phase2-kubernetes

# Create PVC and download model
kubectl apply -f pvc.yaml
kubectl apply -f init-job.yaml
kubectl wait --for=condition=complete job/llm-model-download --timeout=600s

# Deploy inference service
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Step 3: Test

```bash
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
curl -X POST http://$NODE_IP:30080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine", "max_tokens": 100}'
```

### Step 4: Try Scaling (It Won't Work!)

```bash
kubectl scale deployment llm-inference --replicas=3
kubectl get pods  # 2 pods will be Pending!
```

**This demonstrates the K8s GPU limitation!**

## 30-Minute Phase 3 (Run:AI)

### Step 1: Install Run:AI

```bash
# Get license from https://www.run.ai/trial/
helm repo add runai https://run-ai-charts.storage.googleapis.com && helm repo update
kubectl create namespace runai-system
kubectl apply -f runai-license.yaml  # Your license file

helm install runai runai/runai-cluster \
  --namespace runai-system \
  --set runai.clusterName=my-cluster
```

### Step 2: Create Project

```bash
cd ../phase3-runai
kubectl apply -f runai-project.yaml
```

### Step 3: Deploy with GPU Fractions

```bash
kubectl apply -f inference-deployment.yaml

# Watch all 3 pods start on 1 GPU!
kubectl get pods -n runai-llm-inference -w
```

### Step 4: Test

```bash
curl -X POST http://$NODE_IP:30081/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine", "max_tokens": 100}'
```

### Step 5: Load Test

```bash
python3 ../scripts/load_test.py --url http://$NODE_IP:30081/generate --concurrency 15 --requests 150
```

**Expected: 3x throughput vs Phase 2!**

## Results Summary

Fill in your results:

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| GPU Utilization | ___% | ___% | ___% |
| Throughput (req/min) | ___ | ___ | ___ |
| Latency (p50 ms) | ___ | ___ | ___ |
| Pods per GPU | 1 | 1 | 3 |

**Expected**: Phase 3 should show ~3x throughput with 60-80% GPU utilization!

## Troubleshooting

### "CUDA out of memory"
- Use smaller model: `microsoft/Phi-3-mini-4k-instruct`
- Reduce max_tokens in requests

### "nvidia-smi not found"
- Install NVIDIA drivers: https://www.nvidia.com/download/index.aspx

### "Insufficient nvidia.com/gpu" in K8s
- This is expected in Phase 2 when scaling!
- Phase 3 (Run:AI) solves this with GPU fractions

### Pods pending in Phase 3
- Check Run:AI operator: `kubectl get pods -n runai-system`
- Verify license: `kubectl get configmap -n runai-system`

## Next Steps

- Read detailed guides in each phase's README.md
- See [docs/comparison.md](docs/comparison.md) for full analysis
- Join Run:AI community: https://community.run.ai/

## Need Help?

1. Check logs: `kubectl logs <pod-name>`
2. GPU status: `kubectl exec <pod-name> -- nvidia-smi`
3. Run:AI dashboard: https://app.run.ai

Happy learning! 🚀

