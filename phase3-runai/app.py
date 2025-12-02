#!/usr/bin/env python3
"""
Phase 3 - GPU Fraction Test Application
Demonstrates GPU sharing with Run:AI
"""

from flask import Flask, jsonify, request
import subprocess
import os
import socket
import time
from datetime import datetime

app = Flask(__name__)

# Track requests
request_count = 0
start_time = time.time()

def get_gpu_info():
    """Get GPU information using nvidia-smi"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            gpu_data = result.stdout.strip().split(', ')
            return {
                'gpu_name': gpu_data[0],
                'memory_total': gpu_data[1],
                'memory_used': gpu_data[2],
                'utilization': gpu_data[3]
            }
    except Exception as e:
        return {'error': str(e)}
    return {'error': 'GPU not available'}

def get_cuda_processes():
    """Get number of CUDA processes sharing this GPU"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            processes = [p for p in result.stdout.strip().split('\n') if p]
            return len(processes)
    except:
        pass
    return 0

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/generate', methods=['POST'])
def generate():
    """Simulate inference request"""
    global request_count
    request_count += 1
    
    data = request.get_json() or {}
    prompt = data.get('prompt', 'Default prompt')
    max_tokens = data.get('max_tokens', 100)
    
    # Get GPU info
    gpu_info = get_gpu_info()
    cuda_processes = get_cuda_processes()
    
    # Simulate some GPU work (just a tiny CUDA operation)
    # In reality, this would be your LLM inference
    time.sleep(0.1)  # Simulate processing time
    
    response = {
        'prompt': prompt,
        'generated_text': f'[GPU Response from {socket.gethostname()}] Processed: {prompt[:50]}...',
        'max_tokens': max_tokens,
        'pod_name': socket.gethostname(),
        'gpu_info': gpu_info,
        'cuda_processes': cuda_processes,
        'runai_fraction': os.getenv('RUNAI_GPU_FRACTION', 'unknown'),
        'request_number': request_count,
        'uptime_seconds': int(time.time() - start_time)
    }
    
    return jsonify(response)

@app.route('/stats')
def stats():
    """Get pod statistics"""
    gpu_info = get_gpu_info()
    cuda_processes = get_cuda_processes()
    
    return jsonify({
        'pod_name': socket.gethostname(),
        'total_requests': request_count,
        'uptime_seconds': int(time.time() - start_time),
        'gpu_info': gpu_info,
        'cuda_processes_sharing_gpu': cuda_processes,
        'runai_gpu_fraction': os.getenv('RUNAI_GPU_FRACTION', '0.33'),
        'cuda_visible_devices': os.getenv('CUDA_VISIBLE_DEVICES', 'all')
    })

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'Phase 3 - Run:AI GPU Sharing Demo',
        'pod': socket.gethostname(),
        'endpoints': {
            '/health': 'Health check',
            '/generate': 'POST - Simulate inference',
            '/stats': 'GET - Pod statistics',
            '/gpu': 'GET - GPU information'
        }
    })

@app.route('/gpu')
def gpu():
    """Detailed GPU information"""
    gpu_info = get_gpu_info()
    cuda_processes = get_cuda_processes()
    
    return jsonify({
        'gpu_info': gpu_info,
        'cuda_processes': cuda_processes,
        'environment': {
            'CUDA_VISIBLE_DEVICES': os.getenv('CUDA_VISIBLE_DEVICES', 'not set'),
            'RUNAI_GPU_FRACTION': os.getenv('RUNAI_GPU_FRACTION', 'not set'),
            'CUDA_MPS_PIPE_DIRECTORY': os.getenv('CUDA_MPS_PIPE_DIRECTORY', 'not set')
        }
    })

if __name__ == '__main__':
    print(f"Starting GPU test server on {socket.gethostname()}")
    print(f"GPU Fraction: {os.getenv('RUNAI_GPU_FRACTION', 'unknown')}")
    print(f"CUDA Visible Devices: {os.getenv('CUDA_VISIBLE_DEVICES', 'all')}")
    
    app.run(host='0.0.0.0', port=8000, debug=False)

