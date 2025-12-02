#!/bin/bash
# Phase 3 - Build standalone GPU test application

set -e

echo "Building Phase 3 GPU Fraction Demo..."

# Build the Docker image
docker build -t gpu-fraction-demo:phase3 .

echo "✅ Image built successfully: gpu-fraction-demo:phase3"
echo ""
echo "Next steps:"
echo "  kubectl apply -f runai-project.yaml"
echo "  kubectl apply -f inference-deployment.yaml"

