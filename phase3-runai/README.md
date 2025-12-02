# Phase 3: Run:AI - GPU Sharing and Optimization

**This is where the magic happens!** 🎉

Run:AI finally solves the GPU underutilization problem. You'll run **3 inference pods on 1 GPU** with GPU fractions and achieve **3x throughput**!

> **🎊 NEW**: Run:AI is now **open-source** (NVIDIA acquisition, Dec 2024) - no trial or license needed!  
> **📖 Quick Start**: See [INSTALLATION_NOTES.md](INSTALLATION_NOTES.md) for TL;DR version  
> **🔄 Backup Option**: If Run:AI doesn't work, see [ALTERNATIVE_TIME_SLICING.md](ALTERNATIVE_TIME_SLICING.md)

> **📚 Prerequisites**: Complete [Phase 1](../phase1-bare-metal/README.md) and [Phase 2](../phase2-kubernetes/README.md) first.

## ⏱️ Quick Overview

| 🎯 Goal | ⏱️ Time | 📊 Difficulty |
|---------|---------|---------------|
| Share 1 GPU across 3 pods, achieve 3x throughput | 2-3 hours | ⭐⭐⭐⭐ Advanced |

**What you'll achieve**: 
- ✨ **3x throughput** (180 req/min vs 60 in Phase 2)
- ✨ **60-80% GPU utilization** (vs 15-25% in Phase 1 & 2)
- ✨ **67% cost savings** (same hardware, 3x work)

## 🎯 Learning Objectives

- ✅ Install and configure Run:AI operator
- ✅ Use **GPU fractions** to share GPUs between workloads
- ✅ Understand time-slicing and Multi-Process Service (MPS)
- ✅ Implement workload prioritization and fairness policies
- ✅ **Achieve 3x throughput on same hardware**
- ✅ **Prove 67% cost reduction** with real metrics

## 📋 Prerequisites

Before starting, ensure you have:

1. ✅ Kubernetes cluster (from Phase 2)
2. ✅ NVIDIA GPU Operator installed
3. ✅ Phase 2 completed and understood
4. ✅ Helm 3.x installed

### About Run:AI Open-Source

**Great news!** In December 2024, NVIDIA acquired Run:AI for $700M and **open-sourced the platform**. This means:

- ✅ **No trial license needed** - completely free to use
- ✅ **No waiting for approval** - install immediately
- ✅ **Full GPU sharing capabilities** - fractions, time-slicing, MPS
- ✅ **Self-hosted** - complete control over your deployment

You'll install the open-source version directly from the official repository.

## 🚀 Installation Steps

### Step 1: Install Run:AI Operator (Open-Source)

```bash
# Add Run:AI Helm repo
helm repo add runai https://run-ai-charts.storage.googleapis.com
helm repo update

# Create runai-system namespace
kubectl create namespace runai-system

# Install Run:AI cluster (open-source, self-hosted - NO LICENSE NEEDED!)
helm install runai-cluster runai/runai-cluster \
  --namespace runai-system \
  --create-namespace \
  --set controlPlane.selfHosted=true \
  --set cluster.uid=$(uuidgen) \
  --set cluster.url=runai-cluster-runai-system

# Note: No license file needed for open-source version!
```

**Wait for operator pods** (~5 minutes):

```bash
kubectl get pods -n runai-system -w

# Expected output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# runai-scheduler-xxx                     1/1     Running   0          2m
# runai-admission-controller-xxx          1/1     Running   0          2m
# runai-fractional-gpu-xxx                1/1     Running   0          2m
```

**Verify installation**:

```bash
kubectl get crd | grep runai

# Should see Custom Resource Definitions like:
# projects.run.ai
# workloads.run.ai
# departments.run.ai
```

### Step 2: Install Run:AI CLI (Optional)

The CLI is optional for this tutorial - we'll use kubectl with Run:AI CRDs.

**If you want the CLI** (for convenience):

```bash
# For Linux
wget https://github.com/run-ai/runai-cli/releases/latest/download/runai-cli-linux-amd64
chmod +x runai-cli-linux-amd64
sudo mv runai-cli-linux-amd64 /usr/local/bin/runai

# For Windows (PowerShell)
# Download from: https://github.com/run-ai/runai-cli/releases
# Add to PATH

# Verify installation
runai version

# Note: Login not required for self-hosted open-source version
# runai config cluster runai-cluster
```

**For this tutorial, we'll use kubectl directly** - no CLI installation required!

### Step 3: Create Run:AI Project

Create the project using the YAML file:

```bash
# Apply the project configuration
kubectl apply -f runai-project.yaml

# Verify project was created
kubectl get projects.run.ai

# Expected output:
# NAME            GPU QUOTA   AGE
# llm-inference   1.0         5s

# Check project details
kubectl describe project llm-inference
```

The project defines:
- **GPU quota**: 1.0 GPU total
- **GPU fractions enabled**: Can split into 0.33, 0.5, etc.
- **Fairness policy**: Allows over-quota when GPUs idle

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
# Check all pods are running
kubectl get pods -n runai-llm-inference

# Example output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# llm-inference-runai-xxx                 1/1     Running   0          2m
# llm-inference-runai-yyy                 1/1     Running   0          2m
# llm-inference-runai-zzz                 1/1     Running   0          2m

# Optional: If you installed the CLI
# runai list

# Check GPU allocation via annotations
kubectl get pods -n runai-llm-inference -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.runai\.ai/gpu-fraction}{"\n"}{end}'
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

### Run:AI Installation Issues

**Problem**: Helm install fails or pods crash-looping

```bash
# Check pod logs
kubectl logs -n runai-system -l app=runai-scheduler

# Common issues:
# 1. Kubernetes version < 1.20 - upgrade cluster
# 2. NVIDIA GPU Operator not installed - install from Phase 2
# 3. CRD conflicts - remove old installations
```

**Solution**:
```bash
# Reinstall cleanly
helm uninstall runai-cluster -n runai-system
kubectl delete namespace runai-system
# Wait 30 seconds, then retry installation
```

### Pods Stuck in "Pending"

```bash
# Check pod status
kubectl describe pod <pod-name> -n runai-llm-inference

# Check scheduler logs
kubectl logs -n runai-system -l app=runai-scheduler
```

**Common causes**:
1. **Over quota**: Total GPU fractions exceed project quota (check: 3 × 0.33 = 0.99 ≤ 1.0)
2. **Scheduler not running**: Verify `runai-scheduler` pod is Running
3. **GPU not labeled**: Check if nodes have GPU resources
4. **Wrong namespace**: Ensure using `runai-llm-inference` namespace

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
# Check workload priorities in policy
kubectl describe workloadpolicy llm-inference-policy -n runai-llm-inference

# Ensure training job has higher priority than inference
```

### Alternative: NVIDIA GPU Time-Slicing (If Run:AI Doesn't Work)

If you encounter issues with Run:AI, you can achieve similar GPU sharing using **NVIDIA's built-in time-slicing**:

**Step 1: Configure GPU Time-Slicing**

```bash
# Create ConfigMap for time-slicing
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
  namespace: gpu-operator
data:
  any: |-
    version: v1
    sharing:
      timeSlicing:
        replicas: 3
EOF

# Patch GPU Operator to enable time-slicing
kubectl patch clusterpolicy gpu-cluster-policy \
  -n gpu-operator \
  --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": "time-slicing-config"}}}}'
```

**Step 2: Deploy with Standard Kubernetes**

Use the Phase 2 deployment but set `replicas: 3`:

```yaml
# Modified deployment.yaml
spec:
  replicas: 3  # All 3 pods will share 1 GPU
  template:
    spec:
      containers:
      - name: inference
        resources:
          limits:
            nvidia.com/gpu: 1  # Each pod requests 1 GPU (time-sliced)
```

**Trade-offs**:
- ✅ Simpler than Run:AI
- ✅ Built into NVIDIA GPU Operator
- ❌ No advanced scheduling (fairness, priorities)
- ❌ No GPU fractions (can't do 0.33 GPU)
- ❌ Basic time-slicing only (not MPS)

### Getting Help

**Open-Source Run:AI Support**:
- GitHub Issues: https://github.com/run-ai/docs/issues
- Documentation: https://docs.run.ai/
- Community Forums: Search for "Run:AI open source" discussions

**NVIDIA GPU Operator**:
- Documentation: https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/
- Time-Slicing Guide: https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/gpu-sharing.html

## 🆚 Open-Source vs Enterprise Run:AI

**What's Included in Open-Source**:
- ✅ GPU fractions (0.25, 0.33, 0.5, etc.)
- ✅ GPU time-slicing and MPS
- ✅ Basic scheduling and fairness
- ✅ Project quotas
- ✅ Workload management via CRDs
- ✅ CLI tools

**Enterprise-Only Features** (not needed for this tutorial):
- ❌ Web UI dashboard (use kubectl instead)
- ❌ Advanced analytics and reporting
- ❌ Multi-cluster management
- ❌ SSO/LDAP integration
- ❌ Enterprise support

**For learning purposes, open-source provides everything you need!**

## ✅ Phase 3 Complete!

You should now understand:
- ✅ How Run:AI enables GPU fractions
- ✅ GPU time-slicing and MPS
- ✅ **3x throughput on same hardware** (180 vs 60 req/min)
- ✅ **4.8x better GPU utilization** (72% vs 15%)
- ✅ Workload prioritization and preemption
- ✅ **67% cost savings** (1 GPU vs 3 GPUs for same workload)
- ✅ Open-source GPU orchestration (no license required!)

### Key Takeaway

**Run:AI solves the GPU underutilization problem!**

Results:
- ✅ 3 inference pods on 1 GPU (vs 1 pod in Phase 2)
- ✅ 72% GPU utilization (vs 15% in Phase 2)
- ✅ 180 req/min throughput (vs 60 in Phase 2)
- ⚠️ +120ms latency (acceptable trade-off for most use cases)
- ✅ 67% cost reduction

## 🔄 Alternative: NVIDIA GPU Time-Slicing

If Run:AI doesn't work for you, check out **[ALTERNATIVE_TIME_SLICING.md](ALTERNATIVE_TIME_SLICING.md)** for a simpler approach using NVIDIA's built-in GPU time-slicing.

**Quick summary**:
- ✅ Simpler installation (just a ConfigMap)
- ✅ Still achieves 3 pods on 1 GPU
- ❌ No GPU fractions (0.33, etc.)
- ❌ No advanced scheduling

See the full guide: [ALTERNATIVE_TIME_SLICING.md](ALTERNATIVE_TIME_SLICING.md)

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

