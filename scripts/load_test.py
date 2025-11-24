#!/usr/bin/env python3
"""
Load Testing Script for LLM Inference API

Generates concurrent requests to measure throughput, latency, and GPU utilization.

Usage:
    python load_test.py --url http://localhost:8000/generate --concurrency 5 --requests 50
"""

import argparse
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import json
from datetime import datetime


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


async def send_request(
    session: aiohttp.ClientSession,
    url: str,
    prompt: str,
    request_id: int
) -> Dict:
    """Send a single inference request and measure latency"""
    
    payload = {
        "prompt": prompt,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    start_time = time.time()
    
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            result = await response.json()
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000  # Convert to ms
            
            return {
                'request_id': request_id,
                'success': response.status == 200,
                'latency_ms': latency,
                'status_code': response.status,
                'tokens': len(result.get('generated_text', '').split()) if 'generated_text' in result else 0,
                'error': None
            }
    except asyncio.TimeoutError:
        return {
            'request_id': request_id,
            'success': False,
            'latency_ms': 60000,
            'status_code': 0,
            'tokens': 0,
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'request_id': request_id,
            'success': False,
            'latency_ms': 0,
            'status_code': 0,
            'tokens': 0,
            'error': str(e)
        }


async def run_load_test(
    url: str,
    concurrency: int,
    total_requests: int,
    prompts: List[str]
) -> List[Dict]:
    """Run load test with specified concurrency"""
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        # Create request queue
        request_queue = []
        
        for i in range(total_requests):
            prompt = prompts[i % len(prompts)]
            request_queue.append(send_request(session, url, prompt, i))
        
        # Execute requests with concurrency limit
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request(req):
            async with semaphore:
                return await req
        
        print(f"\n{Colors.BOLD}Starting load test...{Colors.END}")
        print(f"  URL: {url}")
        print(f"  Total requests: {total_requests}")
        print(f"  Concurrency: {concurrency}")
        print(f"  Prompts: {len(prompts)} unique\n")
        
        start_time = time.time()
        
        # Run all requests
        results = await asyncio.gather(*[bounded_request(req) for req in request_queue])
        
        end_time = time.time()
        total_time = end_time - start_time
    
    return results, total_time


def print_statistics(results: List[Dict], total_time: float):
    """Calculate and print performance statistics"""
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if not successful:
        print(f"{Colors.RED}All requests failed!{Colors.END}")
        for r in failed[:5]:
            print(f"  Request {r['request_id']}: {r['error']}")
        return
    
    latencies = [r['latency_ms'] for r in successful]
    tokens_generated = [r['tokens'] for r in successful]
    
    # Sort for percentile calculations
    sorted_latencies = sorted(latencies)
    
    # Calculate percentiles
    p50 = sorted_latencies[len(sorted_latencies) // 2]
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}LOAD TEST RESULTS{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    # Success rate
    success_rate = (len(successful) / len(results)) * 100
    print(f"{Colors.BOLD}Success Rate:{Colors.END}")
    print(f"  Total requests: {len(results)}")
    print(f"  Successful: {Colors.GREEN}{len(successful)}{Colors.END}")
    print(f"  Failed: {Colors.RED}{len(failed)}{Colors.END}")
    print(f"  Success rate: {Colors.GREEN}{success_rate:.1f}%{Colors.END}\n")
    
    # Latency statistics
    print(f"{Colors.BOLD}Latency (ms):{Colors.END}")
    print(f"  Min: {Colors.BLUE}{min(latencies):.0f}{Colors.END}")
    print(f"  Max: {Colors.BLUE}{max(latencies):.0f}{Colors.END}")
    print(f"  Mean: {Colors.BLUE}{statistics.mean(latencies):.0f}{Colors.END}")
    print(f"  Median (p50): {Colors.BLUE}{p50:.0f}{Colors.END}")
    print(f"  p95: {Colors.BLUE}{p95:.0f}{Colors.END}")
    print(f"  p99: {Colors.BLUE}{p99:.0f}{Colors.END}\n")
    
    # Throughput
    requests_per_second = len(successful) / total_time
    print(f"{Colors.BOLD}Throughput:{Colors.END}")
    print(f"  Total time: {Colors.BLUE}{total_time:.2f}s{Colors.END}")
    print(f"  Requests/sec: {Colors.BLUE}{requests_per_second:.2f}{Colors.END}")
    print(f"  Requests/min: {Colors.BLUE}{requests_per_second * 60:.0f}{Colors.END}\n")
    
    # Token statistics
    if tokens_generated and sum(tokens_generated) > 0:
        total_tokens = sum(tokens_generated)
        tokens_per_second = total_tokens / total_time
        print(f"{Colors.BOLD}Token Generation:{Colors.END}")
        print(f"  Total tokens: {Colors.BLUE}{total_tokens}{Colors.END}")
        print(f"  Tokens/sec: {Colors.BLUE}{tokens_per_second:.1f}{Colors.END}")
        print(f"  Avg tokens/request: {Colors.BLUE}{statistics.mean(tokens_generated):.0f}{Colors.END}\n")
    
    # Failures
    if failed:
        print(f"{Colors.BOLD}Failures:{Colors.END}")
        error_types = {}
        for r in failed:
            error = r['error'] or f"HTTP {r['status_code']}"
            error_types[error] = error_types.get(error, 0) + 1
        
        for error, count in error_types.items():
            print(f"  {error}: {Colors.RED}{count}{Colors.END}")
        print()
    
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"load_test_results_{timestamp}.json"
    
    summary = {
        'timestamp': timestamp,
        'total_requests': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'success_rate': success_rate,
        'total_time_seconds': total_time,
        'requests_per_second': requests_per_second,
        'latency_ms': {
            'min': min(latencies),
            'max': max(latencies),
            'mean': statistics.mean(latencies),
            'p50': p50,
            'p95': p95,
            'p99': p99
        },
        'detailed_results': results
    }
    
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Results saved to: {Colors.BLUE}{results_file}{Colors.END}\n")


def get_sample_prompts() -> List[str]:
    """Get sample prompts for testing"""
    return [
        "Suggest a skincare routine for dry skin",
        "What are the best hair products for curly hair?",
        "Recommend makeup products for a natural look",
        "What nail care products do you recommend?",
        "Suggest a beauty routine for sensitive skin",
        "What are the trending hair colors this season?",
        "Recommend products for anti-aging skincare",
        "What's the best way to remove makeup?",
        "Suggest products for damaged hair repair",
        "What are essential makeup brushes for beginners?"
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Load test for LLM inference API"
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000/generate',
        help='Inference API endpoint (default: http://localhost:8000/generate)'
    )
    
    parser.add_argument(
        '--concurrency',
        type=int,
        default=5,
        help='Number of concurrent requests (default: 5)'
    )
    
    parser.add_argument(
        '--requests',
        type=int,
        default=50,
        help='Total number of requests to send (default: 50)'
    )
    
    parser.add_argument(
        '--prompts-file',
        type=str,
        default=None,
        help='File with custom prompts (one per line)'
    )
    
    args = parser.parse_args()
    
    # Load prompts
    if args.prompts_file:
        with open(args.prompts_file, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()]
    else:
        prompts = get_sample_prompts()
    
    # Run load test
    results, total_time = asyncio.run(
        run_load_test(args.url, args.concurrency, args.requests, prompts)
    )
    
    # Print statistics
    print_statistics(results, total_time)


if __name__ == "__main__":
    main()

