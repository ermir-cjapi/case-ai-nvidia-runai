# Phase 3 Quick Command Reference

Copy-paste ready commands for Phase 3 installation and testing.

## Prerequisites

Ensure Phase 2 is complete and NVIDIA GPU Operator is installed.

## Installation (5 minutes)

### Step 1: Install Open-Source Run:AI

```bash
# Add Helm repo
helm repo add runai https://run-ai-charts.storage.googleapis.com
helm repo update

# Create required namespaces (runai namespace is needed for RBAC hooks)
kubectl create namespace runai

# Install Run:AI cluster (self-hosted, no license!)
helm install runai-cluster runai/runai-cluster \
  --namespace runai-system \
  --create-namespace \
  --set controlPlane.selfHosted=true \
  --set cluster.uid=$(uuidgen) \
  --set cluster.url=runai-cluster-runai-system

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=runai-scheduler -n runai-system --timeout=300s
```

### Step 2: Verify Installation

```bash
# Check Run:AI pods
kubectl get pods -n runai-system

# Verify CRDs
kubectl get crd | grep runai
```

### Step 3: Create Project and Deploy

```bash
# Navigate to phase3 directory
cd phase3-runai

# Create Run:AI project
kubectl apply -f runai-project.yaml

# Verify project
kubectl get projects.run.ai

# Deploy 3 pods with GPU fractions
kubectl apply -f inference-deployment.yaml

# Watch pods start (all 3 on 1 GPU!)
kubectl get pods -n runai-llm-inference -w
```

## Testing (5 minutes)

### Basic Test

```bash
# Get service info
kubectl get svc -n runai-llm-inference

# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Test inference
curl -X POST http://$NODE_IP:30081/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Suggest a skincare routine for dry skin", "max_tokens": 150}'
```

### Load Test

```bash
# Run load test (from project root)
cd ..
python3 scripts/load_test.py \
  --url http://$NODE_IP:30081/generate \
  --concurrency 15 \
  --requests 150
```

### Verify GPU Sharing

```bash
# Get a pod name
POD_NAME=$(kubectl get pods -n runai-llm-inference -l app=llm-inference-runai -o jsonpath='{.items[0].metadata.name}')

# Check nvidia-smi (should show 3 processes)
kubectl exec -n runai-llm-inference -it $POD_NAME -- nvidia-smi
```

## Monitoring

```bash
# Watch pods
kubectl get pods -n runai-llm-inference -w

# Check pod logs
kubectl logs -n runai-llm-inference <pod-name>

# Check GPU allocation
kubectl get pods -n runai-llm-inference -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.runai\.ai/gpu-fraction}{"\n"}{end}'

# Check Run:AI scheduler logs
kubectl logs -n runai-system -l app=runai-scheduler --tail=50
```

## Troubleshooting

### Clean Reinstall

```bash
# Uninstall everything
kubectl delete -f inference-deployment.yaml
kubectl delete -f runai-project.yaml
helm uninstall runai-cluster -n runai-system
kubectl delete namespace runai-system

# Wait 30 seconds
sleep 30

# Reinstall (start from Step 1 above)
```

### Check GPU Operator

```bash
kubectl get pods -n gpu-operator
kubectl describe node | grep nvidia.com/gpu
```

### View All Resources

```bash
kubectl get all -n runai-llm-inference
kubectl get projects.run.ai
kubectl get crd | grep runai
```

## Cleanup

```bash
# Remove deployment and project
kubectl delete -f inference-deployment.yaml
kubectl delete -f runai-project.yaml

# Uninstall Run:AI
helm uninstall runai-cluster -n runai-system
kubectl delete namespace runai-system
```

## Alternative: NVIDIA Time-Slicing

If Run:AI doesn't work, see [ALTERNATIVE_TIME_SLICING.md](ALTERNATIVE_TIME_SLICING.md) for:

```bash
# Quick time-slicing setup
kubectl apply -f - <<EOF
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

kubectl patch clusterpolicy gpu-cluster-policy \
  -n gpu-operator \
  --type merge \
  -p '{"spec": {"devicePlugin": {"config": {"name": "time-slicing-config", "default": "any"}}}}'
```

## Success Criteria

✅ All 3 pods Running on 1 GPU  
✅ GPU utilization 60-80%  
✅ Throughput ~180 req/min (3x Phase 2)  
✅ All pods respond to requests  

## Next Steps

- Apply policy: `kubectl apply -f policy.yaml`
- Test training job: `kubectl apply -f training-job.yaml`
- See [README.md](README.md) for full guide

