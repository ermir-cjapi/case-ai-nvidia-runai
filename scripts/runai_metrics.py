#!/usr/bin/env python3
"""
Run:AI Metrics Collection Script

Collects and analyzes Run:AI workload metrics for comparison.

Usage:
    python3 runai_metrics.py --project llm-inference --duration 300
"""

import argparse
import subprocess
import json
import time
from datetime import datetime
from typing import List, Dict
import statistics


def run_command(cmd: List[str]) -> str:
    """Execute shell command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return ""


def get_runai_workloads(project: str) -> List[Dict]:
    """Get list of workloads in Run:AI project"""
    # Using kubectl since runai CLI might not have JSON output
    cmd = [
        "kubectl", "get", "pods",
        "-n", f"runai-{project}",
        "-o", "json"
    ]
    
    output = run_command(cmd)
    if not output:
        return []
    
    data = json.loads(output)
    workloads = []
    
    for item in data.get("items", []):
        metadata = item.get("metadata", {})
        annotations = metadata.get("annotations", {})
        
        # Extract Run:AI annotations
        gpu_fraction = annotations.get("runai.ai/gpu-fraction", "0")
        
        workload = {
            "name": metadata.get("name", "unknown"),
            "gpu_fraction": float(gpu_fraction) if gpu_fraction else 0,
            "status": item.get("status", {}).get("phase", "Unknown"),
            "node": item.get("spec", {}).get("nodeName", ""),
        }
        workloads.append(workload)
    
    return workloads


def get_gpu_metrics(pod_name: str, namespace: str) -> Dict:
    """Get GPU metrics from a specific pod"""
    cmd = [
        "kubectl", "exec", "-n", namespace, pod_name, "--",
        "nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
        "--format=csv,noheader,nounits"
    ]
    
    output = run_command(cmd)
    if not output:
        return {}
    
    parts = output.split(",")
    if len(parts) >= 3:
        return {
            "gpu_util": float(parts[0].strip()),
            "memory_used_mb": float(parts[1].strip()),
            "memory_total_mb": float(parts[2].strip())
        }
    
    return {}


def collect_metrics(project: str, duration: int, interval: int = 5):
    """Collect metrics over time"""
    print(f"\n{'='*60}")
    print(f"Collecting Run:AI Metrics for Project: {project}")
    print(f"Duration: {duration} seconds")
    print(f"Interval: {interval} seconds")
    print(f"{'='*60}\n")
    
    namespace = f"runai-{project}"
    samples = []
    iterations = duration // interval
    
    for i in range(iterations):
        timestamp = datetime.now().isoformat()
        print(f"[{i+1}/{iterations}] Collecting sample at {timestamp}")
        
        # Get workloads
        workloads = get_runai_workloads(project)
        
        sample = {
            "timestamp": timestamp,
            "workloads": workloads,
            "gpu_metrics": []
        }
        
        # Get GPU metrics from each pod
        for workload in workloads:
            if workload["status"] == "Running":
                metrics = get_gpu_metrics(workload["name"], namespace)
                if metrics:
                    sample["gpu_metrics"].append({
                        "pod": workload["name"],
                        **metrics
                    })
        
        samples.append(sample)
        
        # Print summary
        if sample["gpu_metrics"]:
            avg_util = statistics.mean([m["gpu_util"] for m in sample["gpu_metrics"]])
            print(f"  Workloads: {len(workloads)} | Avg GPU Util: {avg_util:.1f}%")
        
        if i < iterations - 1:
            time.sleep(interval)
    
    return samples


def analyze_samples(samples: List[Dict]):
    """Analyze collected samples"""
    print(f"\n{'='*60}")
    print("ANALYSIS")
    print(f"{'='*60}\n")
    
    if not samples:
        print("No samples collected!")
        return
    
    # Extract all GPU utilization values
    all_utils = []
    all_memory_used = []
    all_memory_total = []
    
    for sample in samples:
        for metrics in sample["gpu_metrics"]:
            all_utils.append(metrics["gpu_util"])
            all_memory_used.append(metrics["memory_used_mb"])
            all_memory_total.append(metrics["memory_total_mb"])
    
    if not all_utils:
        print("No GPU metrics collected!")
        return
    
    # Calculate statistics
    print("GPU Utilization:")
    print(f"  Min: {min(all_utils):.1f}%")
    print(f"  Max: {max(all_utils):.1f}%")
    print(f"  Mean: {statistics.mean(all_utils):.1f}%")
    print(f"  Median: {statistics.median(all_utils):.1f}%")
    
    if len(all_utils) > 1:
        print(f"  Std Dev: {statistics.stdev(all_utils):.1f}%\n")
    
    # Memory usage
    avg_memory_used = statistics.mean(all_memory_used)
    avg_memory_total = statistics.mean(all_memory_total)
    memory_util = (avg_memory_used / avg_memory_total) * 100
    
    print("GPU Memory:")
    print(f"  Used: {avg_memory_used:.0f} MB ({memory_util:.1f}%)")
    print(f"  Total: {avg_memory_total:.0f} MB\n")
    
    # Workload count
    workload_counts = [len(s["workloads"]) for s in samples]
    avg_workloads = statistics.mean(workload_counts)
    
    print("Workloads:")
    print(f"  Average running: {avg_workloads:.1f}")
    print(f"  Min: {min(workload_counts)}")
    print(f"  Max: {max(workload_counts)}\n")
    
    # GPU fractions
    all_fractions = []
    for sample in samples:
        total_fraction = sum(w["gpu_fraction"] for w in sample["workloads"])
        all_fractions.append(total_fraction)
    
    if all_fractions:
        avg_fraction = statistics.mean(all_fractions)
        print("GPU Allocation:")
        print(f"  Average total fraction: {avg_fraction:.2f}")
        print(f"  Max total fraction: {max(all_fractions):.2f}\n")
    
    # Save results
    results_file = f"runai_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    summary = {
        "project": samples[0].get("project", "unknown"),
        "duration": len(samples) * 5,  # Approximate
        "samples_collected": len(samples),
        "gpu_utilization": {
            "min": min(all_utils),
            "max": max(all_utils),
            "mean": statistics.mean(all_utils),
            "median": statistics.median(all_utils)
        },
        "memory_utilization": {
            "used_mb": avg_memory_used,
            "total_mb": avg_memory_total,
            "percent": memory_util
        },
        "workloads": {
            "average": avg_workloads,
            "min": min(workload_counts),
            "max": max(workload_counts)
        },
        "detailed_samples": samples
    }
    
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Results saved to: {results_file}\n")
    
    # Comparison with Phase 2 (if available)
    print("Comparison to Phase 2 (without Run:AI):")
    print("  Phase 2 GPU Util: ~15-20% (typical)")
    print(f"  Phase 3 GPU Util: {statistics.mean(all_utils):.1f}% (your result)")
    
    improvement = (statistics.mean(all_utils) - 17.5) / 17.5 * 100
    print(f"  Improvement: {improvement:+.1f}%")
    
    if improvement > 200:
        print("  ✅ Excellent! 3-4x better GPU utilization with Run:AI")
    elif improvement > 100:
        print("  ✅ Good! 2-3x better GPU utilization")
    elif improvement > 50:
        print("  ⚠️  Moderate improvement, consider adjusting GPU fractions")
    else:
        print("  ❌ Low improvement, check Run:AI configuration")


def main():
    parser = argparse.ArgumentParser(
        description="Collect Run:AI workload metrics"
    )
    
    parser.add_argument(
        '--project',
        type=str,
        default='llm-inference',
        help='Run:AI project name (default: llm-inference)'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=300,
        help='Duration to collect metrics in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Sampling interval in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Collect metrics
    samples = collect_metrics(args.project, args.duration, args.interval)
    
    # Analyze
    analyze_samples(samples)


if __name__ == "__main__":
    main()

