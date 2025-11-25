# Phase 2: Kubernetes Setup - Clean Approach

## 🎯 What We're Building

In Phase 2, we'll deploy the LLM entirely within Kubernetes using **Kubernetes-native storage and patterns**. Everything will be self-contained in Kubernetes.

## 📦 The Kubernetes Storage Pattern

### How Kubernetes Manages Model Files:

```
┌─────────────────────────────────────────────────────────┐
│ 1. PersistentVolumeClaim (PVC)                          │
│    "I need 20GB of storage for model files"             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Init Job (One-Time Download)                         │
│    "Download model from HuggingFace → Save to PVC"      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Deployment (Main Application)                        │
│    "Run inference pods using model from PVC"            │
└─────────────────────────────────────────────────────────┘
```

## 🗺️ Complete Flow Explained

### Step 1: Create Storage (PVC)

**What is PVC?**
- Like requesting a hard drive in the cloud
- Kubernetes creates storage space for you
- Lives independently of pods (survives restarts)

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: llm-model-storage
spec:
  accessModes:
    - ReadWriteOnce  # One pod can write, others can read
  resources:
    requests:
      storage: 20Gi  # Request 20GB of space
```

**When you run**: `kubectl apply -f pvc.yaml`
- Kubernetes creates a 20GB volume
- You can't see the files directly (they're inside K8s)
- Pods can mount this volume like a USB drive

### Step 2: Download Model (Init-Job)

**What is an Init-Job?**
- A **one-time task** that runs once and exits
- Downloads model from HuggingFace
- Saves it to the PVC
- Never runs again (unless you delete and recreate it)

```yaml
# init-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: llm-model-download
spec:
  template:
    spec:
      containers:
      - name: download
        image: python:3.10-slim
        command:
          - /bin/bash
          - -c
          - |
            # Install dependencies
            pip install transformers huggingface-hub
            
            # Download model
            python3 -c "
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id='meta-llama/Llama-3.2-3B-Instruct',
                local_dir='/model',  # Saves to mounted PVC
                token=os.getenv('HF_TOKEN')
            )
            "
        volumeMounts:
        - name: model-storage
          mountPath: /model  # PVC mounted here
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: llm-model-storage  # Uses the PVC we created
```

**When you run**: `kubectl apply -f init-job.yaml`
1. Kubernetes starts a temporary pod
2. Pod installs Python packages
3. Pod downloads model to `/model` (which is the PVC)
4. Pod completes and exits
5. Model files remain in PVC

**Check progress**: `kubectl logs -f job/llm-model-download`

### Step 3: Deploy Application (Deployment)

**What is a Deployment?**
- Runs your application continuously
- If pod crashes, K8s restarts it automatically
- Can scale to multiple replicas (though we'll see the GPU limitation!)

```yaml
# deployment.yaml (simplified)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference
spec:
  replicas: 1  # Start with 1 pod
  template:
    spec:
      containers:
      - name: inference
        image: your-inference-image
        volumeMounts:
        - name: model-storage
          mountPath: /app/model  # Same PVC, but pod reads from it
          readOnly: true  # Inference only reads, doesn't write
        resources:
          limits:
            nvidia.com/gpu: 1  # Request 1 GPU
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: llm-model-storage  # Same PVC!
```

**When you run**: `kubectl apply -f deployment.yaml`
1. Kubernetes starts your inference pod
2. Mounts the PVC (with model files) at `/app/model`
3. Your app loads the model from `/app/model`
4. Pod keeps running, serving requests

### Step 4: Expose Service (Service)

**What is a Service?**
- Gives your pod a stable network address
- Like a phone number that doesn't change even if you get a new phone (pod)

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-inference
spec:
  type: NodePort
  ports:
  - port: 8000  # Inside K8s
    targetPort: 8000  # Pod port
    nodePort: 30080  # External access port
  selector:
    app: llm-inference  # Routes to pods with this label
```

**When you run**: `kubectl apply -f service.yaml`
- You can access your app at: `http://<node-ip>:30080`
- Even if pod restarts (gets new IP), service stays the same

## 🔄 Complete Deployment Steps

### Step-by-Step Deployment

```bash
cd ~/case-ai-nvidia-runai/phase2-kubernetes

# 1. Create storage (PVC)
kubectl apply -f k8s/pvc.yaml

# Verify PVC is created
kubectl get pvc
# Should show: llm-model-storage   Pending or Bound

# 2. Create HuggingFace token secret
kubectl create secret generic huggingface-token \
  --from-literal=token=hf_your_actual_token_here

# 3. Download model (Init-Job)
kubectl apply -f k8s/init-job.yaml

# Watch the download progress
kubectl logs -f job/llm-model-download

# You'll see:
# - Installing dependencies...
# - Downloading model...
# - Progress bars for each file
# - "Download complete!"

# Wait until job completes
kubectl wait --for=condition=complete job/llm-model-download --timeout=900s

# 4. Build Docker image (IMPORTANT - Required before deployment!)
# 
# WHY? The deployment.yaml references:
#   image: llm-inference:phase2
#   imagePullPolicy: IfNotPresent  ← Checks local Docker first!
#
# Since you're running K8s on the same machine, K8s will look for
# the image in your local Docker. Build it now:

docker build -t llm-inference:phase2 .

# This may take 5-10 minutes
# Verify the image was built
docker images | grep llm-inference
# Should show: llm-inference   phase2   ...

# 5. Deploy configuration
kubectl apply -f k8s/configmap.yaml

# 6. Deploy the inference application
kubectl apply -f k8s/deployment.yaml

# 7. Expose the service
kubectl apply -f k8s/service.yaml

# 8. Watch pod start
kubectl get pods -w

# Wait for: llm-inference-xxx   1/1   Running
# Press Ctrl+C when ready

# 9. Check logs
kubectl logs -f deployment/llm-inference

# Look for:
# - Loading model from /app/model
# - GPU: NVIDIA GeForce RTX 5090
# - Model loaded successfully!
```

### Test the Deployment

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test health
curl http://$NODE_IP:30080/

# Test inference
curl -X POST http://$NODE_IP:30080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine for dry skin", "max_tokens": 150}'
```

## 🔍 Understanding the Architecture

### Where Everything Lives:

```
Kubernetes Cluster (your server)
│
├── Persistent Volume (PVC)
│   └── /model/
│       ├── config.json
│       ├── tokenizer.json
│       ├── model-00001.safetensors
│       └── model-00002.safetensors
│
├── Pod: llm-model-download (Job) - COMPLETED
│   └── Downloaded model → PVC ✅
│
├── Pod: llm-inference-xxx (Deployment) - RUNNING
│   ├── Mounts PVC at /app/model
│   ├── Loads model to GPU
│   └── Serves API on port 8000
│
└── Service: llm-inference
    └── Exposes port 30080 → Pod port 8000
```

### Key Concepts:

1. **PVC (Storage)**: Persistent disk space in Kubernetes
2. **Job (Init-Job)**: One-time task to download model
3. **Deployment**: Keeps your inference pod running
4. **Service**: Network endpoint to access your pod

## 📊 Monitoring Your Deployment

### Check Everything:

```bash
# 1. Check PVC
kubectl get pvc
# STATUS should be "Bound"

# 2. Check Jobs
kubectl get jobs
# llm-model-download should be "Completed"

# 3. Check Pods
kubectl get pods
# llm-inference-xxx should be "Running"

# 4. Check Services
kubectl get svc
# llm-inference should show NodePort 30080

# 5. Check GPU allocation
kubectl describe node | grep -A 10 "Allocated resources"
# Should show: nvidia.com/gpu: 1
```

### View Logs:

```bash
# Job logs (download)
kubectl logs job/llm-model-download

# Deployment logs (inference)
kubectl logs -f deployment/llm-inference

# Specific pod logs
kubectl logs -f llm-inference-xxx
```

## 🎓 What You're Learning

### Kubernetes Patterns:

1. **Persistent Storage**: Model files survive pod restarts
2. **Init Containers/Jobs**: One-time setup tasks
3. **Deployments**: Self-healing applications
4. **Services**: Stable network endpoints
5. **Resource Requests**: GPU scheduling

### The GPU Problem:

```bash
# Try to scale to 2 pods
kubectl scale deployment llm-inference --replicas=2

# Watch what happens
kubectl get pods

# Output:
# llm-inference-xxx-1   1/1     Running
# llm-inference-xxx-2   0/1     Pending   ← Stuck!

# Why?
kubectl describe pod llm-inference-xxx-2

# You'll see:
# Events:
#   Warning  FailedScheduling  0/1 nodes are available:
#            1 Insufficient nvidia.com/gpu
```

**This is the key lesson**: Kubernetes can't share 1 GPU between 2 pods!

## 🧹 Cleanup (When Done)

```bash
# Delete all Phase 2 resources
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
kubectl delete -f configmap.yaml
kubectl delete job llm-model-download
kubectl delete -f pvc.yaml
kubectl delete secret huggingface-token

# Verify everything is gone
kubectl get all
```

## ✅ Phase 2 Complete!

You now understand:
- ✅ Kubernetes storage (PVC)
- ✅ Init-Jobs for setup
- ✅ Deployments for applications
- ✅ Services for networking
- ✅ GPU scheduling in K8s
- ❌ **The limitation**: Can't share GPUs!

**Ready for Phase 3?** Run:AI will solve the GPU sharing problem! 🚀

---

## 🤔 Common Questions

**Q: Why not just copy the model like Phase 1?**
A: This teaches you the **production pattern**. In real deployments, you can't manually copy files to every node.

**Q: Can I see the model files?**
A: Not easily. They're inside K8s storage. But you can exec into a pod:
```bash
kubectl exec -it llm-inference-xxx -- ls -lh /app/model
```

**Q: What if the download fails?**
A: Delete and retry:
```bash
kubectl delete job llm-model-download
kubectl apply -f init-job.yaml
```

**Q: Can I use a different model?**
A: Yes! Edit `init-job.yaml` and change the `MODEL_ID` environment variable.

