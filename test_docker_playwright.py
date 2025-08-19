#!/usr/bin/env python3
"""
Quick Docker Playwright Verification Test
Tests that Playwright works correctly in the Docker container
"""

import requests
import json
import time


def test_docker_playwright():
    """Test Playwright functionality in Docker container"""
    
    print("🐳 Testing Docker Playwright Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8888"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-api-key-123"
    }
    
    # Test cases that should trigger Playwright fallback
    test_cases = [
        {
            "name": "Smyths Toys (likely blocked by requests)",
            "url": "https://www.smythstoys.com/uk/en-gb/toys/sensory-toys/physical-play-sensory-toys/5ft-smoby-life-wave-slide/p/245916",
            "expected_method": "hybrid-playwright"
        },
        {
            "name": "Halfords (should work with requests)",
            "url": "https://www.halfords.com/bikes/hybrid-bikes/boardman-mtx-8.6-mens-hybrid-bike-2021---s-m-l-frames-366006.html",
            "expected_method": "hybrid-requests"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing {test_case['name']}...")
        
        payload = {
            "url": test_case["url"],
            "timeout": 20000,
            "wait_for": "load"
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/api/scrape",
                headers=headers,
                json=payload,
                timeout=25
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    method = data.get('metadata', {}).get('extraction_method', 'unknown')
                    title = data.get('data', {}).get('title', 'N/A')
                    price = data.get('data', {}).get('price', 'N/A')
                    
                    print(f"  ✅ Success - Method: {method}")
                    print(f"    Title: {title[:60]}{'...' if len(title) > 60 else ''}")
                    print(f"    Price: {price}")
                    print(f"    Time: {processing_time}ms")
                    
                    # Check if method matches expectation
                    method_correct = method == test_case['expected_method']
                    if not method_correct:
                        print(f"    ⚠️  Expected {test_case['expected_method']}, got {method}")
                    
                    results.append({
                        "name": test_case["name"],
                        "success": True,
                        "method": method,
                        "expected_method": test_case["expected_method"],
                        "method_correct": method_correct,
                        "processing_time": processing_time,
                        "has_content": bool(title and title != 'N/A'),
                        "error": None
                    })
                else:
                    error_msg = data.get('error', 'Unknown error')
                    print(f"  ❌ Scraping failed: {error_msg}")
                    results.append({
                        "name": test_case["name"],
                        "success": False,
                        "method": "failed",
                        "expected_method": test_case["expected_method"],
                        "method_correct": False,
                        "processing_time": processing_time,
                        "has_content": False,
                        "error": error_msg
                    })
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"  ❌ HTTP Error: {error_msg}")
                results.append({
                    "name": test_case["name"],
                    "success": False,
                    "method": "http_error",
                    "expected_method": test_case["expected_method"],
                    "method_correct": False,
                    "processing_time": processing_time,
                    "has_content": False,
                    "error": error_msg
                })
                
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Request failed: {str(e)}")
            results.append({
                "name": test_case["name"],
                "success": False,
                "method": "exception",
                "expected_method": test_case["expected_method"],
                "method_correct": False,
                "processing_time": processing_time,
                "has_content": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DOCKER PLAYWRIGHT TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    successful_tests = len([r for r in results if r["success"]])
    playwright_tests = len([r for r in results if r["method"] == "hybrid-playwright" and r["success"]])
    requests_tests = len([r for r in results if r["method"] == "hybrid-requests" and r["success"]])
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful Tests: {successful_tests}/{total_tests}")
    print(f"Playwright Tests: {playwright_tests}")
    print(f"Requests Tests: {requests_tests}")
    
    # Verify Playwright functionality
    playwright_working = playwright_tests > 0
    hybrid_system_working = requests_tests > 0 and successful_tests > 0
    
    print(f"\n🎭 Playwright in Docker: {'✅ Working' if playwright_working else '❌ Not Working'}")
    print(f"🚀 Hybrid System: {'✅ Working' if hybrid_system_working else '❌ Not Working'}")
    
    # Detailed results
    print(f"\nDetailed Results:")
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['name']}: {result['method']} ({result['processing_time']}ms)")
        if result["error"]:
            print(f"    Error: {result['error']}")
    
    return {
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "playwright_working": playwright_working,
        "hybrid_system_working": hybrid_system_working,
        "results": results
    }


if __name__ == "__main__":
    test_docker_playwright()