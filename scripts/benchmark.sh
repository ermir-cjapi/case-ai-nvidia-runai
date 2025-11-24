#!/bin/bash
# Automated Benchmarking Script for All Phases

set -e

echo "======================================"
echo "NVIDIA Run:AI Tutorial - Benchmarking"
echo "======================================"
echo ""

# Configuration
CONCURRENCY=5
REQUESTS=50
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results_${TIMESTAMP}"

mkdir -p "$RESULTS_DIR"

# Phase 1: Bare Metal
echo "[1/3] Benchmarking Phase 1 (Bare Metal)..."
echo "  URL: http://localhost:8000/generate"

if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    python3 scripts/load_test.py \
        --url http://localhost:8000/generate \
        --concurrency $CONCURRENCY \
        --requests $REQUESTS \
        > "${RESULTS_DIR}/phase1_results.txt"
    
    echo "  ✅ Phase 1 complete"
else
    echo "  ⚠️  Phase 1 server not running, skipping..."
fi

echo ""

# Phase 2: Kubernetes
echo "[2/3] Benchmarking Phase 2 (Kubernetes)..."

NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "")

if [ -n "$NODE_IP" ]; then
    PHASE2_URL="http://${NODE_IP}:30080/generate"
    echo "  URL: $PHASE2_URL"
    
    if curl -s -f "http://${NODE_IP}:30080/health" > /dev/null 2>&1; then
        python3 scripts/load_test.py \
            --url "$PHASE2_URL" \
            --concurrency $CONCURRENCY \
            --requests $REQUESTS \
            > "${RESULTS_DIR}/phase2_results.txt"
        
        echo "  ✅ Phase 2 complete"
    else
        echo "  ⚠️  Phase 2 server not running, skipping..."
    fi
else
    echo "  ⚠️  Kubernetes not available, skipping..."
fi

echo ""

# Phase 3: Run:AI
echo "[3/3] Benchmarking Phase 3 (Run:AI)..."

if [ -n "$NODE_IP" ]; then
    PHASE3_URL="http://${NODE_IP}:30081/generate"
    echo "  URL: $PHASE3_URL"
    
    if curl -s -f "http://${NODE_IP}:30081/health" > /dev/null 2>&1; then
        python3 scripts/load_test.py \
            --url "$PHASE3_URL" \
            --concurrency 15 \  # Higher concurrency for 3 pods
            --requests 150 \
            > "${RESULTS_DIR}/phase3_results.txt"
        
        echo "  ✅ Phase 3 complete"
    else
        echo "  ⚠️  Phase 3 server not running, skipping..."
    fi
else
    echo "  ⚠️  Kubernetes not available, skipping..."
fi

echo ""
echo "======================================"
echo "Benchmarking Complete!"
echo "Results saved to: $RESULTS_DIR"
echo "======================================"
echo ""

# Compare results
if [ -f "${RESULTS_DIR}/phase1_results.txt" ]; then
    echo "Phase 1 Summary:"
    grep -A 10 "LOAD TEST RESULTS" "${RESULTS_DIR}/phase1_results.txt" | grep -E "(Success rate|Median|Requests/min)" || true
fi

echo ""

if [ -f "${RESULTS_DIR}/phase2_results.txt" ]; then
    echo "Phase 2 Summary:"
    grep -A 10 "LOAD TEST RESULTS" "${RESULTS_DIR}/phase2_results.txt" | grep -E "(Success rate|Median|Requests/min)" || true
fi

echo ""

if [ -f "${RESULTS_DIR}/phase3_results.txt" ]; then
    echo "Phase 3 Summary:"
    grep -A 10 "LOAD TEST RESULTS" "${RESULTS_DIR}/phase3_results.txt" | grep -E "(Success rate|Median|Requests/min)" || true
fi

echo ""
echo "For detailed comparison, see: docs/comparison.md"

