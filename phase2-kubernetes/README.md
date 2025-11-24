# Phase 2: Kubernetes with NVIDIA GPU Operator

This phase deploys the LLM inference service to Kubernetes with GPU scheduling. You'll learn about K8s GPU resource management and discover its limitations for GPU sharing.

## 🎯 Learning Objectives

- Deploy GPU workloads to Kubernetes
- Understand NVIDIA Device Plugin and GPU Operator
- Experience K8s GPU scheduling constraints
- Identify why 1 GPU = 1 pod is inefficient
- Measure GPU utilization with multiple pods (spoiler: still low!)

## 📋 Prerequisites

Before starting, ensure you have:

1. ✅ Kubernetes cluster (K3s, minikube, or full cluster)
2. ✅ kubectl configured and working
3. ✅ NVIDIA GPU node(s) in your cluster
4. ✅ Phase 1 completed (understanding baseline)

### Verify Prerequisites

```bash
# Check kubectl access
kubectl cluster-info

# Check nodes
kubectl get nodes

# Check if GPU operator is installed (we'll install if not)
kubectl get pods -n gpu-operator
```

## 🚀 Installation Steps

### Step 1: Install NVIDIA GPU Operator

The GPU Operator automates GPU setup in Kubernetes.

```bash
# Add NVIDIA Helm repo
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install GPU Operator
helm install --wait --generate-name \
  -n gpu-operator --create-namespace \
  nvidia/gpu-operator \
  --set driver.enabled=false  # Set to true if driver not pre-installed
```

**Wait for operator pods to be ready** (~5 minutes):

```bash
kubectl get pods -n gpu-operator -w
```

### Step 2: Verify GPU Detection

```bash
# Check GPU node capacity
kubectl get nodes -o json | jq '.items[].status.capacity | select(.["nvidia.com/gpu"] != null)'
```

Expected output:
```json
{
  "nvidia.com/gpu": "1"  # or "2", "4", etc.
}
```

### Step 3: Create PersistentVolumeClaim

```bash
cd phase2-kubernetes

# Create PVC for model storage
kubectl apply -f pvc.yaml

# Verify PVC
kubectl get pvc llm-model-storage
```

### Step 4: Download Model to PVC

**Option A: Using Init Job (Recommended)**

```bash
# If using Llama 3.2 3B, create HF token secret first
kubectl create secret generic huggingface-token \
  --from-literal=token=hf_your_token_here

# Or for Phi-3 Mini (no token needed), use:
# Edit init-job.yaml and change MODEL_ID to microsoft/Phi-3-mini-4k-instruct

# Run download job
kubectl apply -f init-job.yaml

# Watch progress
kubectl logs -f job/llm-model-download
```

**Wait for completion** (~10-15 minutes for download).

```bash
# Verify job completed
kubectl get jobs
# NAME                  COMPLETIONS   DURATION   AGE
# llm-model-download    1/1           8m32s      10m
```

**Option B: Copy Model from Local**

If you already have the model from Phase 1:

```bash
# Create a pod to access PVC
kubectl run -it --rm model-copy --image=busybox --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"model-copy","image":"busybox","command":["sleep","3600"],"volumeMounts":[{"name":"model","mountPath":"/model"}]}],"volumes":[{"name":"model","persistentVolumeClaim":{"claimName":"llm-model-storage"}}]}}'

# In another terminal, copy model
kubectl cp ../model/. model-copy:/model/
```

### Step 5: Apply ConfigMap

```bash
kubectl apply -f configmap.yaml
```

### Step 6: Build and Deploy Inference Service

```bash
# Build Docker image
docker build -t llm-inference:phase2 .

# If using remote cluster, push to registry
# docker tag llm-inference:phase2 your-registry/llm-inference:phase2
# docker push your-registry/llm-inference:phase2
# Then update deployment.yaml with full image path

# Deploy
kubectl apply -f deployment.yaml

# Watch pod creation
kubectl get pods -l app=llm-inference -w
```

**Wait for pod to be ready** (~2-3 minutes for model loading):

```bash
kubectl wait --for=condition=ready pod -l app=llm-inference --timeout=300s
```

### Step 7: Expose Service

```bash
kubectl apply -f service.yaml

# Get NodePort
kubectl get svc llm-inference
```

Example output:
```
NAME            TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
llm-inference   NodePort   10.43.123.45    <none>        8000:30080/TCP   1m
```

### Step 8: Test Deployment

```bash
# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test inference
curl -X POST http://$NODE_IP:30080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Suggest a skincare routine for dry skin",
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

**Expected**: Similar response to Phase 1 (latency +50-100ms due to K8s networking).

## 📊 Performance Testing

### Test 1: Single Pod Performance

```bash
# Run load test against K8s service
python3 ../scripts/load_test.py \
  --url http://$NODE_IP:30080/generate \
  --concurrency 5 \
  --requests 50
```

**Record metrics** for comparison.

### Test 2: Monitor GPU Utilization

In a separate terminal:

```bash
# Exec into pod and monitor GPU
POD_NAME=$(kubectl get pods -l app=llm-inference -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it $POD_NAME -- watch -n 1 nvidia-smi
```

**Observe**: GPU utilization still ~15-25% average (idle between requests).

### Test 3: Attempt to Scale

```bash
# Try to scale to 2 replicas
kubectl scale deployment llm-inference --replicas=2

# Watch what happens
kubectl get pods -l app=llm-inference -w
```

**What you'll see**:

If you have **1 GPU**:
- ✅ First pod: Running
- ❌ Second pod: **Pending** (insufficient nvidia.com/gpu)

```bash
kubectl describe pod <pending-pod-name>
# Events: 0/1 nodes are available: 1 Insufficient nvidia.com/gpu
```

**Key insight**: Can't run 2 pods if each requests 1 full GPU!

If you have **2 GPUs**:
- ✅ Both pods running
- But: Each GPU still idle 75-85% of the time
- **Double the waste!**

## 🔍 Analysis

### Problem 1: GPU Fragmentation

**Scenario**: You have 1 GPU and want to run 3 inference pods.

**K8s behavior**:
- Each pod requests `nvidia.com/gpu: 1` (full GPU)
- K8s can only schedule 1 pod per GPU
- Pods 2 and 3: **Pending forever**

**Why**: Kubernetes treats GPUs as discrete, non-divisible resources.

### Problem 2: GPU Still Underutilized

Even with successful deployment:

| Metric | Phase 1 | Phase 2 | Change |
|--------|---------|---------|--------|
| **GPU Utilization** | 15-25% | 10-20% | ❌ **Worse!** |
| **Latency (p50)** | ~800ms | ~850ms | +50ms (K8s overhead) |
| **Throughput** | 60 req/min | 60 req/min | No improvement |
| **Pods per GPU** | 1 | 1 | No change |

**Conclusion**: Kubernetes doesn't solve the GPU idle problem!

### Problem 3: HPA Doesn't Help

Try applying HPA:

```bash
kubectl apply -f hpa.yaml

# Watch HPA
kubectl get hpa -w
```

**Issue**: HPA scales based on CPU/memory, but bottleneck is GPU availability.
- CPU/memory at 50%? HPA wants to scale up.
- No free GPUs? New pod stays **Pending**.

## 📝 Exercises

### Exercise 1: GPU Resource Limits

Try removing GPU limit:

```yaml
resources:
  requests:
    nvidia.com/gpu: 1
  # No limits
```

**Question**: Does this allow multiple pods per GPU? Why or why not?

### Exercise 2: Measure Networking Overhead

Compare Phase 1 vs Phase 2 latency:

```bash
# Phase 1 (local Docker)
curl http://localhost:8000/generate ...

# Phase 2 (K8s NodePort)
curl http://$NODE_IP:30080/generate ...
```

**Question**: How much latency does K8s networking add?

### Exercise 3: Pod Affinity

Try forcing 2 pods on same node (if you have 2 GPUs on one node):

Edit deployment.yaml, add:

```yaml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: llm-inference
      topologyKey: kubernetes.io/hostname
```

**Question**: Do both pods get scheduled? What's the total GPU utilization?

## 🛠️ Troubleshooting

### Pod Stuck in "Pending"

```bash
kubectl describe pod <pod-name>
```

**Common causes**:
1. **Insufficient nvidia.com/gpu**: Not enough GPUs
2. **Node taints**: GPU nodes have taints, add tolerations
3. **Node selector mismatch**: Adjust nodeSelector in deployment

### "CUDA out of memory" in Pod

**Solution**: Reduce `resources.requests.memory` or use smaller model.

### Model Not Found

```bash
# Check PVC contents
kubectl run -it --rm debug --image=busybox --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"debug","image":"busybox","command":["ls","-la","/model"],"volumeMounts":[{"name":"model","mountPath":"/model"}]}],"volumes":[{"name":"model","persistentVolumeClaim":{"claimName":"llm-model-storage"}}]}}'
```

### GPU Operator Pods Failing

```bash
kubectl get pods -n gpu-operator
kubectl logs -n gpu-operator <failing-pod>
```

**Common fix**: Ensure NVIDIA drivers installed on nodes.

## 📊 Key Metrics to Record

| Metric | Value | Notes |
|--------|-------|-------|
| **Pods Running** | ___ | Max possible on your GPUs |
| **GPU Utilization (avg)** | ___% | Still low! |
| **Latency (p50)** | ___ms | vs Phase 1 |
| **Throughput** | ___ req/min | Same as Phase 1? |
| **Pending Pods** | ___ | Due to GPU limits |

## ✅ Phase 2 Complete!

You should now understand:
- ✅ How to deploy GPU workloads to Kubernetes
- ✅ NVIDIA GPU Operator functionality
- ✅ **K8s GPU limitation: 1 pod = 1 GPU** (no sharing!)
- ✅ HPA doesn't solve GPU underutilization
- ✅ Kubernetes adds overhead without improving GPU efficiency

### Key Takeaway

**Kubernetes doesn't solve the GPU idle problem!**

You still have:
- 75-85% GPU idle time
- Can't run multiple inference pods per GPU
- GPU fragmentation (pending pods)
- Same throughput as Phase 1, but with K8s complexity

## Next Steps

Continue to **[Phase 3: Run:AI](../phase3-runai/README.md)** to:
- Enable GPU fractions (0.3-0.5 GPU per pod)
- Run 3 pods on 1 GPU with time-slicing
- Achieve 60-80% GPU utilization (vs 15-25% now!)
- See **3x throughput improvement** on same hardware!

**This is where the magic happens!** 🚀

