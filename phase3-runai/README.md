# Phase 3: Run:AI - GPU Sharing and Optimization

This phase demonstrates Run:AI's advanced GPU management capabilities. You'll finally solve the GPU underutilization problem by running **3 inference pods on 1 GPU** with GPU fractions!

## 🎯 Learning Objectives

- Install and configure Run:AI operator
- Use GPU fractions to share GPUs between workloads
- Understand time-slicing and Multi-Process Service (MPS)
- Implement workload prioritization and fairness policies
- **Achieve 3x throughput on same hardware** vs Phase 2!
- Measure 60-80% GPU utilization (vs 15-25% in Phase 1 & 2)

## 📋 Prerequisites

Before starting, ensure you have:

1. ✅ Run:AI account (sign up at https://www.run.ai/trial/)
2. ✅ Kubernetes cluster (from Phase 2)
3. ✅ NVIDIA GPU Operator installed
4. ✅ Phase 2 completed and understood

### Get Run:AI License

1. Sign up: https://www.run.ai/trial/
2. Request trial license (usually approved within 24 hours)
3. Download license file (`runai-license.yaml`)

## 🚀 Installation Steps

### Step 1: Install Run:AI Operator

```bash
# Add Run:AI Helm repo
helm repo add runai https://run-ai-charts.storage.googleapis.com
helm repo update

# Create runai-system namespace
kubectl create namespace runai-system

# Apply license (get from Run:AI)
kubectl apply -f runai-license.yaml

# Install Run:AI control plane
helm install runai runai/runai-cluster \
  --namespace runai-system \
  --set runai.clusterName=my-cluster \
  --set runai.controlPlane.url=https://app.run.ai
```

**Wait for operator pods** (~5 minutes):

```bash
kubectl get pods -n runai-system -w
```

### Step 2: Install Run:AI CLI

```bash
# Download CLI
wget https://github.com/run-ai/runai-cli/releases/latest/download/runai-cli-linux-amd64
chmod +x runai-cli-linux-amd64
sudo mv runai-cli-linux-amd64 /usr/local/bin/runai

# Verify installation
runai version

# Login
runai login
```

### Step 3: Create Run:AI Project

```bash
# Method 1: Using CLI
runai project create llm-inference \
  --gpu-quota 1 \
  --cpu-quota 8 \
  --memory-quota 32Gi

# Method 2: Using YAML
kubectl apply -f runai-project.yaml

# Verify project
runai project list
```

Expected output:
```
Project           GPU Quota   GPU Allocated   GPU Utilization
llm-inference     1.0         0.0             0%
```

### Step 4: Enable GPU Fractions

Run:AI supports GPU fractions automatically, but verify:

```bash
# Check Run:AI config
kubectl get configmap runai-public -n runai-system -o yaml | grep fractions

# Should show: allow-fractions: "true"
```

### Step 5: Deploy Inference with GPU Fractions

```bash
cd phase3-runai

# Deploy 3 pods, each with 0.33 GPU fraction
kubectl apply -f inference-deployment.yaml

# Watch pods starting
kubectl get pods -n runai-llm-inference -w
```

**Key difference from Phase 2**: All 3 pods will start on **1 GPU**!

```bash
# Verify all pods running
kubectl get pods -n runai-llm-inference
```

Expected:
```
NAME                                    READY   STATUS    RESTARTS   AGE
llm-inference-runai-xxx                 1/1     Running   0          2m
llm-inference-runai-yyy                 1/1     Running   0          2m
llm-inference-runai-zzz                 1/1     Running   0          2m
```

### Step 6: Verify GPU Sharing

```bash
# Check Run:AI workloads
runai list

# Example output:
# NAME                      PROJECT         GPU ALLOCATED   GPU UTILIZATION   STATUS
# llm-inference-runai-xxx   llm-inference   0.33           45%               Running
# llm-inference-runai-yyy   llm-inference   0.33           38%               Running
# llm-inference-runai-zzz   llm-inference   0.33           42%               Running
```

**Key insight**: 3 pods sharing 1 GPU (0.33 + 0.33 + 0.33 = 0.99 ≈ 1.0)

### Step 7: Monitor GPU Utilization

```bash
# Exec into any pod
POD_NAME=$(kubectl get pods -n runai-llm-inference -l app=llm-inference-runai -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n runai-llm-inference -it $POD_NAME -- nvidia-smi
```

**Observe**: GPU now shows **multiple processes** (MPS enabled)!

```
+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   PID   Type   Process name                            GPU Memory     |
|  0     123   C      /usr/bin/python3                        2.3G           |
|  0     456   C      /usr/bin/python3                        2.3G           |
|  0     789   C      /usr/bin/python3                        2.3G           |
+-----------------------------------------------------------------------------+
```

### Step 8: Apply Fairness Policies

```bash
kubectl apply -f policy.yaml

# Verify policy
runai describe project llm-inference
```

## 📊 Performance Testing

### Test 1: Distributed Load Test

Now we have **3 pods** serving traffic:

```bash
# Get service NodePort
kubectl get svc -n runai-llm-inference llm-inference-runai

NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Run load test (higher concurrency now possible!)
python3 ../scripts/load_test.py \
  --url http://$NODE_IP:30081/generate \
  --concurrency 15 \  # 5 requests per pod
  --requests 150
```

**Expected results**:
- Throughput: ~180 req/min (vs 60 in Phase 2)
- **3x improvement!**
- Latency: ~900ms (slight increase due to GPU sharing)

### Test 2: GPU Utilization Measurement

While load testing, monitor GPU:

```bash
kubectl exec -n runai-llm-inference -it $POD_NAME -- watch -n 1 nvidia-smi
```

**Observe**:
- GPU utilization: **60-80%** (vs 15-25% in Phase 2!)
- All 3 processes active
- GPU memory efficiently shared

### Test 3: Workload Preemption

Submit a high-priority training job:

```bash
kubectl apply -f training-job.yaml

# Watch what happens
runai list -w
```

**Expected behavior**:
1. Training job requests 0.5 GPU
2. Total allocation: 3×0.33 + 0.5 = 1.49 > 1.0 GPU quota
3. Run:AI **preempts** one inference pod (lowest priority)
4. Training job starts
5. When training completes, inference pod restarts

## 🔍 Analysis & Comparison

### Performance Comparison Table

| Metric | Phase 1 | Phase 2 | Phase 3 | Improvement |
|--------|---------|---------|---------|-------------|
| **GPU Utilization (avg)** | 18% | 15% | **72%** | **4.8x** ✅ |
| **Pods per GPU** | 1 | 1 | **3** | **3x** ✅ |
| **Throughput (req/min)** | 60 | 60 | **180** | **3x** ✅ |
| **Latency (p50)** | 800ms | 850ms | 920ms | +120ms ⚠️ |
| **Latency (p95)** | 1100ms | 1200ms | 1350ms | +250ms ⚠️ |
| **Pods Pending** | 0 | 2 (if scaled) | **0** | ✅ |
| **GPU Memory Waste** | High | High | **Low** | ✅ |

### Cost Efficiency

**Scenario**: You need to serve 180 requests/min

**Without Run:AI (Phase 2)**:
- Need **3 GPUs** (1 pod per GPU, 60 req/min each)
- GPU utilization: 15% per GPU
- **Cost: 3× GPU price**
- **Waste: 85% of GPU capacity idle**

**With Run:AI (Phase 3)**:
- Need **1 GPU** (3 pods sharing, 60 req/min each)
- GPU utilization: 72%
- **Cost: 1× GPU price**
- **Savings: 67% cost reduction!**

### Latency Trade-off

**Latency increased by ~120ms** (800ms → 920ms)

**Why**:
- GPU context switching between processes
- Time-slicing overhead
- Shared GPU memory bandwidth

**Is it worth it**?
- ✅ **Yes** for most inference workloads:
  - 120ms additional latency (15% increase)
  - **3x throughput increase**
  - **67% cost savings**
- ❌ **No** for ultra-low-latency applications (<100ms requirement)

## 📝 Advanced Features

### Feature 1: Dynamic GPU Allocation

Run:AI can dynamically adjust GPU allocation:

```bash
# Submit job with minimum and maximum GPU
runai submit dynamic-inference \
  --project llm-inference \
  --gpu 0.25-0.75 \  # Min 0.25, max 0.75
  --image llm-inference:phase2 \
  --service-type nodeport \
  --port 8000:30082

# Run:AI allocates based on demand
# Low traffic: 0.25 GPU
# High traffic: scales up to 0.75 GPU
```

### Feature 2: GPU Pools

Group GPUs by type:

```bash
# Create GPU pools
kubectl label nodes gpu-node-1 runai/gpu-pool=inference
kubectl label nodes gpu-node-2 runai/gpu-pool=training

# Deploy to specific pool
runai submit inference \
  --project llm-inference \
  --gpu 0.5 \
  --node-pool inference  # Only use inference pool
```

### Feature 3: Multi-Instance GPU (MIG)

For A100/A30 GPUs:

```bash
# Enable MIG on A100
sudo nvidia-smi -i 0 -mig 1

# Create MIG instances (e.g., 3×3g.20gb)
sudo nvidia-smi mig -cgi 9,9,9 -C

# Run:AI automatically uses MIG instances
runai submit mig-inference \
  --project llm-inference \
  --gpu-mig-profile 3g.20gb
```

**Benefit**: Hardware isolation (better than time-slicing for production)

## 🛠️ Troubleshooting

### Pods Stuck in "Pending"

```bash
runai describe workload <pod-name>
```

**Common causes**:
1. **Over quota**: Total GPU fractions exceed project quota
2. **MPS not enabled**: Check Run:AI config
3. **GPU memory limit**: Reduce per-pod memory

### GPU Memory Errors with 3 Pods

Each pod loads ~7GB model, but shares 1 GPU:

**Solution**: Use model caching or reduce memory:

```yaml
env:
- name: PYTORCH_CUDA_ALLOC_CONF
  value: "max_split_size_mb:512"  # Better memory management
```

### Lower Than Expected GPU Utilization

```bash
# Check Run:AI scheduler logs
kubectl logs -n runai-system deployment/runai-scheduler
```

**Common fixes**:
- Increase load test concurrency
- Adjust time-slicing interval in policy
- Enable MPS if not already

### Preemption Not Working

```bash
# Check workload priorities
runai list --show-priority

# Ensure high-priority workloads have priority > low-priority
```

## ✅ Phase 3 Complete!

You should now understand:
- ✅ How Run:AI enables GPU fractions
- ✅ GPU time-slicing and MPS
- ✅ **3x throughput on same hardware** (180 vs 60 req/min)
- ✅ **4.8x better GPU utilization** (72% vs 15%)
- ✅ Workload prioritization and preemption
- ✅ **67% cost savings** (1 GPU vs 3 GPUs for same workload)

### Key Takeaway

**Run:AI solves the GPU underutilization problem!**

Results:
- ✅ 3 inference pods on 1 GPU (vs 1 pod in Phase 2)
- ✅ 72% GPU utilization (vs 15% in Phase 2)
- ✅ 180 req/min throughput (vs 60 in Phase 2)
- ⚠️ +120ms latency (acceptable trade-off for most use cases)
- ✅ 67% cost reduction

## 📚 Next Steps

### Production Deployment

1. **Enable monitoring**:
   ```bash
   # Run:AI dashboard
   https://app.run.ai
   
   # Prometheus metrics
   kubectl get svc -n runai-system runai-prometheus
   ```

2. **Set up autoscaling**:
   ```bash
   runai submit autoscale-inference \
     --min-replicas 2 \
     --max-replicas 6 \
     --scale-metric requests-per-second \
     --scale-target 100
   ```

3. **Implement model versioning**:
   - Blue-green deployments
   - A/B testing with traffic splitting
   - Canary releases

### Learning Resources

- Run:AI Documentation: https://docs.run.ai/
- GPU Optimization Guide: https://docs.run.ai/admin/researcher-setup/optimize-gpu-utilization/
- MPS vs MIG Comparison: https://docs.nvidia.com/datacenter/tesla/mps-user-guide/

## 🎉 Tutorial Complete!

Congratulations! You've completed all 3 phases and learned:

1. **Phase 1**: Direct GPU inference (baseline)
2. **Phase 2**: Kubernetes GPU scheduling (limitations)
3. **Phase 3**: Run:AI GPU optimization (**3x improvement**)

**Key Learning**: Advanced GPU orchestration tools like Run:AI are essential for efficient GPU utilization in production ML deployments!

