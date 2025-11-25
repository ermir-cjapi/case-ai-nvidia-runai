# Phase 2: Kubernetes with NVIDIA GPU Operator

Deploy the LLM inference service to Kubernetes with GPU scheduling. You'll discover that traditional K8s doesn't solve the GPU idle time problem!

> **📚 Prerequisites**: Complete [Phase 1](../phase1-bare-metal/README.md) first to understand baseline GPU performance.

## ⏱️ Quick Overview

| 🎯 Goal | ⏱️ Time | 📊 Difficulty |
|---------|---------|---------------|
| Deploy to K8s, try to scale, discover limitations | 1-2 hours | ⭐⭐⭐ Medium |

**What you'll discover**: Kubernetes treats GPUs as indivisible! You still can't share one GPU between multiple pods. 😞

---

## 📖 Documentation

**🌟 START HERE**: [SETUP_GUIDE_CLEAN.md](SETUP_GUIDE_CLEAN.md)

This comprehensive guide explains:
- ✅ Kubernetes concepts (PVC, Jobs, Deployments, Services)
- ✅ Complete step-by-step deployment
- ✅ What each manifest file does
- ✅ How everything connects together
- ✅ The GPU sharing limitation

---

## 🎯 Learning Objectives

- ✅ Deploy GPU workloads to Kubernetes
- ✅ Understand NVIDIA Device Plugin and GPU Operator
- ✅ Use Kubernetes storage (PVC) for model files
- ✅ Experience K8s GPU scheduling constraints (1 GPU = 1 pod)
- ✅ Try to scale and see pods stuck in "Pending"
- ✅ Measure GPU utilization (spoiler: still only 15-20%!)

---

## 🚀 Quick Start (TL;DR)

```bash
cd ~/case-ai-nvidia-runai/phase2-kubernetes

# 1. Stop Phase 1
cd ../phase1-bare-metal && docker-compose down && cd ../phase2-kubernetes

# 2. Install GPU Operator
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia && helm repo update
helm install gpu-operator nvidia/gpu-operator -n gpu-operator --create-namespace --set driver.enabled=false

# 3. Create storage
kubectl apply -f k8s/pvc.yaml

# 4. Create HF token secret
kubectl create secret generic huggingface-token --from-literal=token=hf_YOUR_TOKEN

# 5. Download model (takes ~10-15 min)
kubectl apply -f k8s/init-job.yaml
kubectl logs -f job/llm-model-download  # Watch progress

# 6. Build Docker image (IMPORTANT!)
docker build -t llm-inference:phase2 .

# Verify image exists
docker images | grep llm-inference

# 7. Deploy application
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 8. Test
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
curl http://$NODE_IP:30080/
```

**For detailed explanations of each step, see [SETUP_GUIDE_CLEAN.md](SETUP_GUIDE_CLEAN.md)**

---

## 📁 Files in This Directory

### Documentation:
| File | Purpose |
|------|---------|
| **SETUP_GUIDE_CLEAN.md** | 🌟 Complete walkthrough with explanations |
| **README.md** | This file - quick reference |

### Application Code:
| File | Purpose |
|------|---------|
| **Dockerfile** | Container image definition |
| **app.py** | Inference server code (imports from Phase 1) |
| **model_loader.py** | Model loading code (imports from Phase 1) |
| **requirements.txt** | Python dependencies |

### Kubernetes Manifests (k8s/):
| File | Purpose |
|------|---------|
| **pvc.yaml** | Creates 20GB storage for model files |
| **init-job.yaml** | One-time job to download model from HuggingFace |
| **configmap.yaml** | Configuration settings |
| **deployment.yaml** | Main inference application |
| **service.yaml** | Exposes API on NodePort 30080 |
| **hpa.yaml** | Horizontal Pod Autoscaler (advanced, optional) |

---

## 🔍 What Each Manifest Does

### k8s/pvc.yaml - Persistent Storage
Creates 20GB of storage in Kubernetes for model files. Think of it as a virtual hard drive.

```bash
kubectl apply -f k8s/pvc.yaml
kubectl get pvc  # Should show "Bound"
```

### k8s/init-job.yaml - Model Download
A one-time job that downloads the model from HuggingFace and saves it to the PVC.

```bash
kubectl apply -f k8s/init-job.yaml
kubectl logs -f job/llm-model-download  # Watch download
```

### k8s/deployment.yaml - Inference Application
Runs your inference pods. Mounts the PVC to access model files. Requests 1 GPU.

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods  # Should show "Running"
```

### k8s/service.yaml - Network Access
Exposes your application on port 30080 so you can access it.

```bash
kubectl apply -f k8s/service.yaml
kubectl get svc  # Shows NodePort
```

---

## 🧪 Testing

### Health Check
```bash
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
curl http://$NODE_IP:30080/
```

### Inference Test
```bash
curl -X POST http://$NODE_IP:30080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine for dry skin", "max_tokens": 150}'
```

### Load Test
```bash
cd ..
source venv/bin/activate
python3 scripts/load_test.py --url http://$NODE_IP:30080/generate --concurrency 5 --requests 50
```

---

## 🔬 Demonstrating the GPU Limitation

### Try to Scale (This Will Fail!)

```bash
# Try to create 2 pods
kubectl scale deployment llm-inference --replicas=2

# Watch what happens
kubectl get pods

# Output:
# llm-inference-xxx-1   1/1     Running
# llm-inference-xxx-2   0/1     Pending   ← Stuck! Can't get GPU

# See why
kubectl describe pod llm-inference-xxx-2 | grep -A 5 "Events:"

# You'll see:
# Warning  FailedScheduling  Insufficient nvidia.com/gpu
```

**This is the key lesson**: Kubernetes can't share 1 GPU between 2 pods!

### Scale Back
```bash
kubectl scale deployment llm-inference --replicas=1
```

---

## 📊 Expected Results

| Metric | Phase 1 (Docker) | Phase 2 (K8s) | Change |
|--------|------------------|---------------|--------|
| Throughput (req/min) | ~73 | ~60-70 | ~Same |
| Latency p50 (ms) | ~4133 | ~4200 | Slightly higher |
| GPU Utilization (avg) | ~18% | ~15-20% | **No improvement!** |
| Pods per GPU | 1 | 1 | **No improvement!** |
| Complexity | Low | High | Increased |

**Key Insight**: Adding Kubernetes orchestration doesn't solve the GPU efficiency problem!

---

## 🛠️ Troubleshooting

### Pod Stuck in Pending
```bash
kubectl describe pod <pod-name>

# Common issues:
# 1. GPU Operator not ready: kubectl get pods -n gpu-operator
# 2. PVC not bound: kubectl get pvc
# 3. Model not downloaded: kubectl logs job/llm-model-download
```

### Init-Job Failed
```bash
kubectl logs job/llm-model-download

# Common issues:
# 1. Invalid HF token
# 2. Network timeout
# 3. Insufficient PVC space

# Fix and retry:
kubectl delete job llm-model-download
kubectl apply -f init-job.yaml
```

### GPU Out of Memory
```bash
# Check what's using GPU
nvidia-smi

# Stop Phase 1 or NIM
docker-compose down  # or docker stop <nim-container>

# Delete and recreate pod
kubectl delete pod <pod-name>
```

### Can't Access NodePort
```bash
# Check service
kubectl get svc llm-inference

# Check pod is running
kubectl get pods

# Check logs
kubectl logs <pod-name>

# Try with localhost if on same machine
curl http://localhost:30080/
```

---

## 🧹 Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete job llm-model-download
kubectl delete -f k8s/pvc.yaml
kubectl delete secret huggingface-token

# Verify
kubectl get all
```

---

## ✅ Phase 2 Complete!

You now understand:
- ✅ Kubernetes deployment patterns
- ✅ GPU scheduling in K8s
- ✅ Persistent storage (PVC)
- ✅ Init-Jobs for setup tasks
- ❌ **The limitation**: K8s can't share GPUs between pods!
- ❌ **The problem**: GPU utilization is still low (~15-20%)

**Key Takeaway**: Orchestration alone doesn't solve GPU efficiency!

---

## 🚀 Next: Phase 3

**Phase 3 (Run:AI)** will solve the GPU sharing problem:
- ✅ Run **3 pods on 1 GPU**
- ✅ Achieve **~220 req/min** (3x throughput)
- ✅ Get **60-75% GPU utilization**
- ✅ Save **67% on GPU costs**

Continue to [Phase 3](../phase3-runai/README.md)

---

## 📚 Additional Resources

- [Kubernetes GPU Docs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [K8s Storage Concepts](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

