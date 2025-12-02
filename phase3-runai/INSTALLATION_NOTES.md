# Phase 3 Installation Notes - Open-Source Run:AI

## Important Update (December 2024)

🎉 **Run:AI is now open-source!** Following NVIDIA's $700M acquisition, Run:AI has been released as open-source software.

### What This Means for You

✅ **No trial signup required** - Install directly from Helm charts  
✅ **No license file needed** - Use `--set controlPlane.selfHosted=true`  
✅ **Free forever** - Open-source under permissive license  
✅ **All core features available** - GPU fractions, time-slicing, MPS  

### Quick Installation

```bash
# Install open-source Run:AI
helm repo add runai https://run-ai-charts.storage.googleapis.com
helm repo update

# Create required runai namespace (needed for RBAC pre-install hooks)
kubectl create namespace runai

# Install Run:AI cluster
helm install runai-cluster runai/runai-cluster \
  --namespace runai-system \
  --create-namespace \
  --set controlPlane.selfHosted=true \
  --set cluster.uid=$(uuidgen) \
  --set cluster.url=runai-cluster-runai-system
```

No license file, no waiting for approval, no credit card!

## Documentation Structure

- **[README.md](README.md)** - Main Phase 3 guide (updated for open-source)
- **[ALTERNATIVE_TIME_SLICING.md](ALTERNATIVE_TIME_SLICING.md)** - Backup option if Run:AI doesn't work
- **INSTALLATION_NOTES.md** (this file) - Quick reference

## Files in This Directory

All YAML files are compatible with open-source Run:AI:

1. **runai-project.yaml** - Creates project with GPU quota
2. **inference-deployment.yaml** - 3 pods sharing 1 GPU (0.33 each)
3. **policy.yaml** - Fairness and priority policies
4. **training-job.yaml** - Example training workload with preemption

## Installation Flow

```
1. Install NVIDIA GPU Operator (Phase 2)
   ↓
2. Install Run:AI cluster (open-source)
   ↓
3. Create Run:AI project
   ↓
4. Deploy inference with GPU fractions
   ↓
5. Test and benchmark (3x throughput!)
```

## Troubleshooting

### If Run:AI installation fails:

1. **Check Kubernetes version**: Must be ≥ 1.20
   ```bash
   kubectl version --short
   ```

2. **Check GPU Operator**: Must be installed first
   ```bash
   kubectl get pods -n gpu-operator
   ```

3. **Clean reinstall**:
   ```bash
   helm uninstall runai-cluster -n runai-system
   kubectl delete namespace runai-system
   # Wait 30 seconds, then retry
   ```

### If you can't get Run:AI working:

Use **NVIDIA GPU time-slicing** instead - see [ALTERNATIVE_TIME_SLICING.md](ALTERNATIVE_TIME_SLICING.md)

## Support Resources

- **Open-source docs**: https://docs.run.ai/
- **GitHub repository**: https://github.com/run-ai/docs
- **GitHub issues**: https://github.com/run-ai/docs/issues
- **NVIDIA GPU Operator**: https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/

## What Changed from Original Tutorial

| Original | Updated (Open-Source) |
|----------|----------------------|
| Trial signup required | ❌ Not needed |
| License file required | ❌ Not needed |
| Cloud control plane | ✅ Self-hosted |
| Web UI dashboard | ⚠️ Use kubectl instead |
| `runai` CLI login | ⚠️ No login needed |
| Enterprise features | ✅ Core features available |

## Features Available in Open-Source

✅ **Available**:
- GPU fractions (0.25, 0.33, 0.5, etc.)
- Time-slicing
- Multi-Process Service (MPS)
- Project quotas
- Basic fairness policies
- Workload priorities
- CLI tools

⚠️ **Enterprise-Only** (not needed for tutorial):
- Web UI dashboard
- Advanced analytics
- Multi-cluster management
- SSO/LDAP integration
- Professional support

## Expected Results (Same as Before!)

Even with open-source, you'll achieve:

- ✅ **3x throughput** (180 req/min vs 60)
- ✅ **72% GPU utilization** (vs 15% in Phase 2)
- ✅ **67% cost savings** (1 GPU vs 3 GPUs)
- ✅ **3 pods on 1 GPU** (GPU fractions working)

The open-source version provides all the capabilities needed for learning and production use!

## Questions?

1. Read the main [README.md](README.md) for detailed guide
2. Check [ALTERNATIVE_TIME_SLICING.md](ALTERNATIVE_TIME_SLICING.md) for backup option
3. Open GitHub issue: https://github.com/run-ai/docs/issues
4. Check NVIDIA documentation: https://docs.nvidia.com/datacenter/cloud-native/

Happy learning! 🚀

