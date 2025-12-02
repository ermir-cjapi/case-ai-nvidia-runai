#!/bin/bash
# Phase 3 - Test GPU sharing

set -e

# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
SERVICE_URL="http://$NODE_IP:30081"

echo "Testing GPU Fraction Demo at $SERVICE_URL"
echo ""

# Test health endpoint
echo "1. Health Check:"
curl -s $SERVICE_URL/health | jq '.'
echo ""

# Test GPU info
echo "2. GPU Information:"
curl -s $SERVICE_URL/gpu | jq '.'
echo ""

# Test stats
echo "3. Pod Statistics:"
curl -s $SERVICE_URL/stats | jq '.'
echo ""

# Test inference simulation
echo "4. Simulate Inference Request:"
curl -s -X POST $SERVICE_URL/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Test GPU sharing with Run:AI", "max_tokens": 100}' | jq '.'
echo ""

echo "✅ All tests completed!"
echo ""
echo "To see which pods are serving requests, run multiple times:"
echo "  for i in {1..10}; do curl -s $SERVICE_URL/stats | jq -r .pod_name; done"

