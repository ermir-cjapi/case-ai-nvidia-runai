#!/usr/bin/env python3
"""
GPU Validation Script for NVIDIA Run:AI Tutorial

This script checks your NVIDIA GPU setup and verifies all requirements
for running the LLM inference tutorial.

Usage:
    python3 gpu_check.py
"""

import subprocess
import sys
import json
from typing import Dict, List, Tuple


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """Run a shell command and return success status and output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def check_nvidia_smi() -> bool:
    """Check if nvidia-smi is available"""
    print(f"\n{Colors.BOLD}[1/7] Checking nvidia-smi...{Colors.END}")
    success, output = run_command(['nvidia-smi', '--version'])
    
    if success:
        print(f"{Colors.GREEN}✓ nvidia-smi found{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}✗ nvidia-smi not found{Colors.END}")
        print(f"{Colors.YELLOW}  → Install NVIDIA drivers: https://www.nvidia.com/download/index.aspx{Colors.END}")
        return False


def check_gpu_details() -> Dict:
    """Get GPU details using nvidia-smi"""
    print(f"\n{Colors.BOLD}[2/7] Checking GPU details...{Colors.END}")
    
    # Query GPU details (without cuda_version which is not a valid field)
    success, output = run_command([
        'nvidia-smi',
        '--query-gpu=name,memory.total,driver_version',
        '--format=csv,noheader'
    ])
    
    if not success:
        print(f"{Colors.RED}✗ Could not query GPU details{Colors.END}")
        return {}
    
    # Parse output (format: "GPU Name, 24576 MiB, 535.129.03")
    parts = output.split(',')
    if len(parts) >= 3:
        gpu_name = parts[0].strip()
        memory_str = parts[1].strip()
        driver_version = parts[2].strip()
        
        # Extract memory in MB
        memory_mb = int(memory_str.split()[0])
        memory_gb = memory_mb / 1024
        
        # Get CUDA version separately from nvidia-smi output
        cuda_version = "N/A"
        cuda_success, cuda_output = run_command(['nvidia-smi'])
        if cuda_success:
            import re
            cuda_match = re.search(r'CUDA Version:\s+(\d+\.\d+)', cuda_output)
            if cuda_match:
                cuda_version = cuda_match.group(1)
        
        print(f"{Colors.GREEN}✓ GPU detected{Colors.END}")
        print(f"  Name: {Colors.BLUE}{gpu_name}{Colors.END}")
        print(f"  Memory: {Colors.BLUE}{memory_gb:.1f} GB{Colors.END}")
        print(f"  Driver: {Colors.BLUE}{driver_version}{Colors.END}")
        print(f"  CUDA: {Colors.BLUE}{cuda_version}{Colors.END}")
        
        # Check if memory is sufficient (10GB minimum for Llama 3.2 3B)
        if memory_gb < 10:
            print(f"{Colors.YELLOW}  ⚠ Warning: GPU has less than 10GB VRAM{Colors.END}")
            print(f"{Colors.YELLOW}  → Consider using Phi-3 Mini with quantization{Colors.END}")
        
        return {
            'name': gpu_name,
            'memory_gb': memory_gb,
            'driver_version': driver_version,
            'cuda_version': cuda_version
        }
    
    return {}


def check_cuda_compiler() -> bool:
    """Check if NVCC (CUDA compiler) is available"""
    print(f"\n{Colors.BOLD}[3/7] Checking CUDA compiler (nvcc)...{Colors.END}")
    
    success, output = run_command(['nvcc', '--version'])
    
    if success:
        # Extract CUDA version from output
        for line in output.split('\n'):
            if 'release' in line.lower():
                print(f"{Colors.GREEN}✓ NVCC found{Colors.END}")
                print(f"  {Colors.BLUE}{line.strip()}{Colors.END}")
                return True
        print(f"{Colors.GREEN}✓ NVCC found{Colors.END}")
        return True
    else:
        print(f"{Colors.YELLOW}⚠ NVCC not found (optional for runtime){Colors.END}")
        print(f"{Colors.YELLOW}  → CUDA Toolkit not required for inference, only for development{Colors.END}")
        return False


def check_docker() -> bool:
    """Check if Docker is installed"""
    print(f"\n{Colors.BOLD}[4/7] Checking Docker...{Colors.END}")
    
    success, output = run_command(['docker', '--version'])
    
    if success:
        print(f"{Colors.GREEN}✓ Docker found{Colors.END}")
        print(f"  {Colors.BLUE}{output}{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}✗ Docker not found{Colors.END}")
        print(f"{Colors.YELLOW}  → Install Docker: https://docs.docker.com/get-docker/{Colors.END}")
        return False


def check_docker_nvidia_runtime() -> bool:
    """Check if NVIDIA Container Toolkit is installed"""
    print(f"\n{Colors.BOLD}[5/7] Checking NVIDIA Container Toolkit...{Colors.END}")
    
    # Try to run a simple NVIDIA container
    success, output = run_command([
        'docker', 'run', '--rm', '--gpus', 'all',
        'nvidia/cuda:12.2.0-base-ubuntu22.04',
        'nvidia-smi', '-L'
    ])
    
    if success:
        print(f"{Colors.GREEN}✓ NVIDIA Container Toolkit working{Colors.END}")
        print(f"  {Colors.BLUE}{output.split(chr(10))[0]}{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}✗ NVIDIA Container Toolkit not working{Colors.END}")
        print(f"{Colors.YELLOW}  → Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html{Colors.END}")
        return False


def check_kubectl() -> bool:
    """Check if kubectl is installed (for Phase 2 & 3)"""
    print(f"\n{Colors.BOLD}[6/7] Checking kubectl (for Phase 2 & 3)...{Colors.END}")
    
    success, output = run_command(['kubectl', 'version', '--client', '--short'])
    
    if success:
        print(f"{Colors.GREEN}✓ kubectl found{Colors.END}")
        # Try to get cluster info
        cluster_success, _ = run_command(['kubectl', 'cluster-info'])
        if cluster_success:
            print(f"{Colors.GREEN}✓ Kubernetes cluster accessible{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠ kubectl found but cluster not accessible{Colors.END}")
            print(f"{Colors.YELLOW}  → Configure kubectl or skip to Phase 1 only{Colors.END}")
        return True
    else:
        print(f"{Colors.YELLOW}⚠ kubectl not found (required for Phase 2 & 3){Colors.END}")
        print(f"{Colors.YELLOW}  → Install: https://kubernetes.io/docs/tasks/tools/{Colors.END}")
        return False


def check_python_packages() -> bool:
    """Check if required Python packages are available"""
    print(f"\n{Colors.BOLD}[7/7] Checking Python packages...{Colors.END}")
    
    required_packages = ['torch', 'transformers', 'fastapi', 'uvicorn']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"{Colors.GREEN}✓ {package} installed{Colors.END}")
        except ImportError:
            print(f"{Colors.YELLOW}⚠ {package} not installed{Colors.END}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n{Colors.YELLOW}Install missing packages:{Colors.END}")
        print(f"  pip install {' '.join(missing_packages)}")
        print(f"  or use the Dockerfiles provided in each phase")
        return False
    
    return True


def print_summary(results: Dict[str, bool], gpu_info: Dict):
    """Print overall summary and recommendations"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    # Count passed checks
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    # Phase readiness
    phase1_ready = results['nvidia_smi'] and results['docker'] and results['nvidia_docker']
    phase2_ready = phase1_ready and results['kubectl']
    
    print(f"Checks passed: {Colors.BLUE}{passed}/{total}{Colors.END}\n")
    
    # Phase 1
    if phase1_ready:
        print(f"{Colors.GREEN}✓ Ready for Phase 1 (Bare Metal){Colors.END}")
    else:
        print(f"{Colors.RED}✗ Not ready for Phase 1{Colors.END}")
        print(f"{Colors.YELLOW}  → Fix: nvidia-smi, Docker, NVIDIA Container Toolkit{Colors.END}")
    
    # Phase 2 & 3
    if phase2_ready:
        print(f"{Colors.GREEN}✓ Ready for Phase 2 & 3 (Kubernetes/Run:AI){Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠ Not ready for Phase 2 & 3{Colors.END}")
        print(f"{Colors.YELLOW}  → Install kubectl and configure K8s cluster{Colors.END}")
    
    # GPU recommendations
    if gpu_info:
        print(f"\n{Colors.BOLD}Recommended Model:{Colors.END}")
        memory_gb = gpu_info.get('memory_gb', 0)
        
        if memory_gb >= 12:
            print(f"{Colors.GREEN}  → Llama 3.2 3B (FP16) - Optimal{Colors.END}")
        elif memory_gb >= 10:
            print(f"{Colors.BLUE}  → Llama 3.2 3B (FP16) - Should work{Colors.END}")
        elif memory_gb >= 8:
            print(f"{Colors.YELLOW}  → Phi-3 Mini with INT8 quantization{Colors.END}")
        else:
            print(f"{Colors.RED}  → GPU memory too low for this tutorial{Colors.END}")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    if phase1_ready:
        print(f"  1. Download model: python3 scripts/download_model.py")
        print(f"  2. Start Phase 1: cd phase1-bare-metal && docker build -t llm-inference:phase1 .")
    else:
        print(f"  1. Fix missing requirements above")
        print(f"  2. Re-run this script to verify")
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}\n")


def main():
    """Main execution"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}NVIDIA Run:AI Tutorial - GPU Environment Check{Colors.END}\n")
    
    results = {}
    gpu_info = {}
    
    # Run all checks
    results['nvidia_smi'] = check_nvidia_smi()
    
    if results['nvidia_smi']:
        gpu_info = check_gpu_details()
    
    results['cuda_compiler'] = check_cuda_compiler()
    results['docker'] = check_docker()
    
    if results['docker']:
        results['nvidia_docker'] = check_docker_nvidia_runtime()
    else:
        results['nvidia_docker'] = False
    
    results['kubectl'] = check_kubectl()
    results['python_packages'] = check_python_packages()
    
    # Print summary
    print_summary(results, gpu_info)
    
    # Exit code based on Phase 1 readiness
    phase1_ready = results['nvidia_smi'] and results['docker'] and results['nvidia_docker']
    sys.exit(0 if phase1_ready else 1)


if __name__ == "__main__":
    main()

