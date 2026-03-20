#!/usr/bin/env python3
"""
Benchmark script for testing inference speed on the Jetson Nano.
Usage: python3 scripts/benchmark.py [--endpoint URL]
"""

import argparse
import io
import json
import time
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8000"


def benchmark_request(method, url, data=None, content_type=None, iterations=10):
    """Benchmark a single endpoint."""
    times = []
    last_response = None

    for i in range(iterations):
        req = urllib.request.Request(url, data=data, method=method)
        if content_type:
            req.add_header("Content-Type", content_type)

        start = time.time()
        try:
            with urllib.request.urlopen(req) as resp:
                last_response = json.loads(resp.read())
        except urllib.error.URLError as e:
            print(f"  Error: {e}")
            return None
        elapsed = time.time() - start
        times.append(elapsed)

    avg = sum(times) / len(times)
    min_t = min(times)
    max_t = max(times)
    print(
        f"  Avg: {avg * 1000:.1f}ms | Min: {min_t * 1000:.1f}ms | Max: {max_t * 1000:.1f}ms | Runs: {iterations}"
    )
    return last_response


def create_test_image():
    """Create a small test image in memory."""
    try:
        from PIL import Image

        img = Image.new("RGB", (640, 480), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        print("  Pillow not installed, skipping image benchmarks")
        return None


def build_multipart(image_bytes):
    """Build a simple multipart/form-data body."""
    boundary = "----BenchmarkBoundary"
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode()
        + image_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def main():
    parser = argparse.ArgumentParser(description="Benchmark Jetson AI Server")
    parser.add_argument("--url", default=BASE_URL, help="Server base URL")
    parser.add_argument("-n", type=int, default=10, help="Number of iterations")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    n = args.n

    print(f"Benchmarking {base} ({n} iterations each)\n")

    # Health check
    print("[Health Check]")
    benchmark_request("GET", f"{base}/health", iterations=1)
    print()

    # Image classification
    image_bytes = create_test_image()
    if image_bytes:
        body, ct = build_multipart(image_bytes)

        print("[Image Classification - POST /image/classify]")
        result = benchmark_request(
            "POST", f"{base}/image/classify", data=body, content_type=ct, iterations=n
        )
        if result:
            print(f"  Top prediction: {result['predictions'][0]}")
        print()

        print("[Object Detection - POST /image/detect]")
        result = benchmark_request(
            "POST", f"{base}/image/detect", data=body, content_type=ct, iterations=n
        )
        if result:
            print(f"  Detections: {len(result['detections'])}")
        print()

    # Text embeddings
    print("[Text Embeddings - POST /text/embeddings]")
    payload = json.dumps({"text": "The quick brown fox jumps over the lazy dog"}).encode()
    result = benchmark_request(
        "POST",
        f"{base}/text/embeddings",
        data=payload,
        content_type="application/json",
        iterations=n,
    )
    if result:
        print(f"  Dimensions: {result['dimensions']}")
    print()

    # Text similarity
    print("[Text Similarity - POST /text/similarity]")
    payload = json.dumps(
        {"text1": "The cat sat on the mat", "text2": "A feline rested on the rug"}
    ).encode()
    result = benchmark_request(
        "POST",
        f"{base}/text/similarity",
        data=payload,
        content_type="application/json",
        iterations=n,
    )
    if result:
        print(f"  Similarity: {result['similarity']}")
    print()

    # System info
    print("[System Info - GET /system/info]")
    result = benchmark_request("GET", f"{base}/system/info", iterations=1)
    if result:
        mem = result.get("memory", {})
        print(
            f"  RAM: {mem.get('used_percent', '?')}% used ({mem.get('available_mb', '?')}MB free)"
        )
    print()


if __name__ == "__main__":
    main()
