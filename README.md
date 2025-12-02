# NVIDIA Run:AI Learning Tutorial - LLM Inference with Llama 3.2 3B

A comprehensive, hands-on tutorial demonstrating GPU-accelerated LLM inference deployment across three progressively advanced approaches:

1. **Phase 1**: Direct NVIDIA GPU inference (bare metal)
2. **Phase 2**: Kubernetes deployment with GPU scheduling
3. **Phase 3**: Run:AI orchestration with advanced GPU sharing

## 🎯 Learning Objectives

By completing this tutorial, you will understand:

- GPU memory management for LLM inference
- CUDA optimization and performance tuning
- Kubernetes GPU resource scheduling and limitations
- Run:AI GPU fractions and time-slicing
- Real-world cost efficiency improvements (2-3x better GPU utilization)

## 🚀 Use Case: Customer Service LLM API

**Model**: Llama 3.2 3B (3 billion parameters, ~7GB VRAM)
**Task**: Product recommendations, FAQ responses, personalized content generation
**API**: FastAPI with streaming text generation

## 📁 Project Structure

```
case-ai-nvidia-runai/
├── phase1-bare-metal/          # Direct GPU inference
│   ├── app.py                  # FastAPI inference server
│   ├── model_loader.py         # GPU model loading
│   ├── Dockerfile              # NVIDIA CUDA image
│   ├── requirements.txt
│   └── README.md
├── phase2-kubernetes/          # K8s deployment
│   ├── Dockerfile
│   ├── deployment.yaml         # GPU pod deployment
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── pvc.yaml                # Model storage
│   ├── init-job.yaml           # Model download job
│   └── README.md
├── phase3-runai/               # Run:AI integration
│   ├── runai-project.yaml
│   ├── inference-deployment.yaml
│   ├── training-job.yaml
│   ├── policy.yaml
│   └── README.md
├── scripts/
│   ├── gpu_check.py            # GPU validation
│   ├── download_model.py       # HuggingFace model download
│   ├── load_test.py            # Performance benchmarking
│   └── runai_metrics.py        # Run:AI metrics collection
├── docs/
│   ├── phase1-guide.md
│   ├── phase2-guide.md
│   ├── phase3-guide.md
│   └── comparison.md
└── model/                      # Model weights (gitignored)
```

## ✅ Prerequisites

### Hardware Requirements
- NVIDIA GPU with **10GB+ VRAM** (RTX 3080, A10, A100, etc.)
- NVIDIA Driver 520+ (for CUDA 12.2)

### Software Requirements
- Docker with NVIDIA Container Toolkit
- Kubernetes cluster (K3s, minikube, or full cluster)
- kubectl configured
- Helm 3.x (for Phase 3)
- Python 3.10+
- HuggingFace account (free)

**Note for Phase 3**: Run:AI is now open-source (NVIDIA acquisition, Dec 2024) - no trial license needed!

### Verify GPU Setup

```bash
# Check GPU availability
nvidia-smi

# Expected output: GPU name, memory (10GB+), driver version 520+
```

## 🏃 Quick Start

### Step 0: Clone This Repository

**Important**: GitHub requires a Personal Access Token (PAT), not your password.

**Option A - Using Personal Access Token**:

```bash
# 1. Create token at: https://github.com/settings/tokens
# 2. Clone the repo (replace YOUR_USERNAME with your GitHub username)
git clone https://github.com/YOUR_USERNAME/case-ai-nvidia-runai.git
# Enter your username and use the PAT as password
```

**Option B - Using SSH**:

```bash
# 1. Add SSH key to GitHub: https://github.com/settings/keys
# 2. Clone using SSH (replace YOUR_USERNAME with your GitHub username)
git clone git@github.com:YOUR_USERNAME/case-ai-nvidia-runai.git
```

**Option C - Download ZIP** (no Git needed):

```bash
# Replace YOUR_USERNAME with your GitHub username
wget https://github.com/YOUR_USERNAME/case-ai-nvidia-runai/archive/refs/heads/main.zip
unzip main.zip && cd case-ai-nvidia-runai-main
```

### Step 1: Verify GPU

```bash
cd case-ai-nvidia-runai  # or case-ai-nvidia-runai-main if downloaded as ZIP
python3 scripts/gpu_check.py
```

### Step 2: Download Model

```bash
# Requires HuggingFace token (https://huggingface.co/settings/tokens)
python3 scripts/download_model.py --model meta-llama/Llama-3.2-3B-Instruct --output ./model
```

### Step 3: Run Phase 1 - Bare Metal Inference

Navigate to Phase 1 and start the inference server:

```bash
cd phase1-bare-metal

# Start the service (easiest method)
docker-compose up -d

# View logs to confirm it's running
docker-compose logs -f
```

Wait for the model to load (~30-60 seconds), then test it:

```bash
# Test the inference API
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine for dry skin", "max_tokens": 200}'
```

### Step 4: Benchmark Phase 1 Performance

```bash
# Go back to project root
cd ..

# Run load test
python3 scripts/load_test.py --url http://localhost:8000/generate --concurrency 5 --requests 50
```

**📝 Record your metrics** - you'll compare them in Phase 2 and 3!

### Step 5: Phase 2 - Kubernetes

```bash
cd phase2-kubernetes

# Install NVIDIA GPU Operator (one-time)
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/gpu-operator/main/deployments/gpu-operator.yaml

# Deploy inference service
kubectl apply -f pvc.yaml
kubectl apply -f init-job.yaml  # Wait for completion
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Test via NodePort
kubectl get svc llm-inference
curl -X POST http://<node-ip>:<nodeport>/generate -d '{"prompt": "..."}'
```

### Step 6: Phase 3 - Run:AI (Open-Source)

```bash
cd phase3-runai

# Install Run:AI operator (open-source - NO LICENSE NEEDED!)
helm repo add runai https://run-ai-charts.storage.googleapis.com
helm install runai-cluster runai/runai-cluster \
  --namespace runai-system \
  --create-namespace \
  --set controlPlane.selfHosted=true

# Create Run:AI project
kubectl apply -f runai-project.yaml

# Deploy with GPU fractions (3 pods on 1 GPU!)
kubectl apply -f inference-deployment.yaml

# Monitor workloads
kubectl get pods -n runai-llm-inference
```

**Note**: Run:AI was open-sourced by NVIDIA in December 2024 - no trial signup required!

## 📊 Expected Results

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| **GPU Utilization** | 15-25% | 10-20% | 60-80% |
| **Pods per GPU** | 1 | 1 | 3 |
| **Latency (p50)** | 800ms | 850ms | 900ms |
| **Throughput** | 60 req/min | 60 req/min | 180 req/min |
| **Cost Efficiency** | Baseline | Same | **3x better** |

## 📚 Documentation

- [Phase 1: Bare Metal Guide](docs/phase1-guide.md)
- [Phase 2: Kubernetes Guide](docs/phase2-guide.md)
- [Phase 3: Run:AI Guide](docs/phase3-guide.md)
- [Performance Comparison](docs/comparison.md)

## 🐛 Troubleshooting

### GPU not detected
```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### Out of memory errors
- Use Phi-3 Mini instead (smaller): `microsoft/Phi-3-mini-4k-instruct`
- Enable INT8 quantization in `model_loader.py`

### Kubernetes GPU not scheduling
```bash
# Verify GPU operator
kubectl get pods -n gpu-operator-resources

# Check node GPU capacity
kubectl get nodes -o json | jq '.items[].status.capacity'
```

## 📖 Learning Path

1. **Day 1**: Complete Phase 1, understand GPU memory and CUDA basics
2. **Day 2**: Complete Phase 2, learn K8s GPU scheduling limitations
3. **Day 3**: Complete Phase 3, see Run:AI efficiency improvements

## 🤝 Contributing

This is a learning tutorial. Feel free to:
- Add support for other models (Mistral, Qwen, etc.)
- Implement INT8/INT4 quantization
- Add Prometheus metrics exporters
- Create Grafana dashboards

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Resources

- [NVIDIA GPU Operator Docs](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html)
- [Run:AI Documentation](https://docs.run.ai/)
- [Llama 3.2 Model Card](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
- [Transformers GPU Guide](https://huggingface.co/docs/transformers/perf_infer_gpu_one)

## 💬 Support

For issues with:
- **Phase 1**: Check CUDA/Docker setup
- **Phase 2**: Verify NVIDIA GPU Operator installation
- **Phase 3**: Ensure Run:AI license is active

## Next Steps

After completing this tutorial, you can:
- Deploy in production with auto-scaling
- Implement model versioning (A/B testing)
- Add monitoring with Prometheus/Grafana
- Integrate with API gateways (Kong, NGINX)

