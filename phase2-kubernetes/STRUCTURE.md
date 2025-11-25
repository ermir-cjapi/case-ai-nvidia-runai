# Phase 2 Directory Structure

## 📁 Clean Organization

```
phase2-kubernetes/
│
├── 📖 Documentation
│   ├── SETUP_GUIDE_CLEAN.md    🌟 Start here - complete walkthrough
│   ├── README.md                Quick reference & troubleshooting
│   └── STRUCTURE.md             This file - directory layout
│
├── 🐍 Application Code
│   ├── app.py                   FastAPI inference server
│   ├── model_loader.py          Model loading logic
│   ├── requirements.txt         Python dependencies
│   └── Dockerfile               Container image definition
│
└── ☸️  Kubernetes Manifests (k8s/)
    ├── pvc.yaml                 Storage (20GB for model files)
    ├── init-job.yaml            Model download job (one-time)
    ├── configmap.yaml           Application configuration
    ├── deployment.yaml          Inference pods
    ├── service.yaml             Network access (NodePort 30080)
    └── hpa.yaml                 Autoscaler (optional, advanced)
```

## 🎯 Why This Structure?

### Separation of Concerns:
- **Documentation** = Learning and reference
- **Application Code** = What runs in the container
- **k8s/** = Kubernetes configuration (manifests)

### Benefits:
1. ✅ **Clear organization** - Easy to find files
2. ✅ **Logical grouping** - Related files together
3. ✅ **Standard practice** - Common in real projects
4. ✅ **Easier to maintain** - Add/remove manifests without clutter

## 🚀 How to Use

### Deploy Everything:

```bash
cd ~/case-ai-nvidia-runai/phase2-kubernetes

# Apply all K8s manifests in order
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/init-job.yaml        # Wait for completion
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Or Apply All at Once:

```bash
# Apply all manifests in the k8s directory
kubectl apply -f k8s/
```

**Note**: The order matters for the first deployment (PVC must exist before Job), but `kubectl apply -f k8s/` will retry dependencies automatically.

## 📝 File Purposes

### Documentation Files:

| File | When to Read |
|------|--------------|
| **SETUP_GUIDE_CLEAN.md** | First time - explains everything |
| **README.md** | Quick commands, troubleshooting |
| **STRUCTURE.md** | Understanding the layout (this file) |

### Application Files:

| File | Purpose |
|------|---------|
| **app.py** | FastAPI server with `/generate` endpoint |
| **model_loader.py** | Loads LLM to GPU memory |
| **requirements.txt** | FastAPI, transformers, torch, etc. |
| **Dockerfile** | Builds the container image |

### Kubernetes Manifests (k8s/):

| File | What It Creates | When It Runs |
|------|----------------|--------------|
| **pvc.yaml** | 20GB storage volume | Once (persists) |
| **init-job.yaml** | Model download job | Once (then completes) |
| **configmap.yaml** | Environment config | Once (can update) |
| **deployment.yaml** | Inference pods | Continuous (keeps running) |
| **service.yaml** | NodePort access | Once (persists) |
| **hpa.yaml** | Autoscaler | Optional (for scaling) |

## 🔄 Workflow

### Initial Setup:
```bash
# 1. Install GPU Operator (one-time)
helm install gpu-operator nvidia/gpu-operator ...

# 2. Deploy Phase 2
kubectl apply -f k8s/pvc.yaml
kubectl create secret generic huggingface-token --from-literal=token=...
kubectl apply -f k8s/init-job.yaml
# Wait for model download...
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Testing:
```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test API
curl http://$NODE_IP:30080/
```

### Cleanup:
```bash
kubectl delete -f k8s/
kubectl delete secret huggingface-token
```

## 💡 Tips

### Viewing Logs:
```bash
# Job logs (model download)
kubectl logs job/llm-model-download

# Deployment logs (inference)
kubectl logs -f deployment/llm-inference

# Specific pod
kubectl logs -f <pod-name>
```

### Editing Manifests:
```bash
# Edit a manifest
nano k8s/deployment.yaml  # or vim, code, etc.

# Apply changes
kubectl apply -f k8s/deployment.yaml

# K8s will update the running resources
```

### Check Resources:
```bash
# All resources
kubectl get all

# Specific types
kubectl get pvc
kubectl get jobs
kubectl get pods
kubectl get svc
```

## 🎓 Learning Path

1. **Read SETUP_GUIDE_CLEAN.md** - Understand concepts
2. **Deploy step-by-step** - Following the guide
3. **Test and verify** - Make sure it works
4. **Try to scale** - Demonstrate GPU limitation
5. **Compare with Phase 1** - Same GPU waste!
6. **Move to Phase 3** - Run:AI solves this

## ✅ Success Criteria

After Phase 2, you should understand:
- ✅ How Kubernetes storage works (PVC)
- ✅ How one-time jobs work (init-job)
- ✅ How deployments work (continuous apps)
- ✅ How services expose apps (networking)
- ✅ **The limitation**: Can't share GPUs!
- ✅ **The problem**: Still low GPU utilization!

---

**Ready to start?** Go to [SETUP_GUIDE_CLEAN.md](SETUP_GUIDE_CLEAN.md)!

