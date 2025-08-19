#!/usr/bin/env python3
"""
Docker Integration Test Suite for Scrapiee
Tests the Docker container functionality against the full test suite
"""

import asyncio
import json
import time
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class TestCase:
    """API test case definition"""
    site_name: str
    url: str
    expected_price: str
    expected_currency: str = "GBP"


# Test cases from examples.md
TEST_CASES = [
    TestCase("Halfords", "https://www.halfords.com/bikes/hybrid-bikes/boardman-mtx-8.6-mens-hybrid-bike-2021---s-m-l-frames-366006.html", "£600"),
    TestCase("Decathlon", "https://www.decathlon.co.uk/p/4-man-inflatable-blackout-tent-air-seconds-4-1/_/R-p-302837?mc=8648382&c=cappuccino%20beige", "£299.99"),
    TestCase("John Lewis", "https://www.johnlewis.com/john-lewis-handheld-foldable-desk-fan-4-inch/white/p5873998", "£12"),
    TestCase("Amazon UK", "https://www.amazon.co.uk/dp/B0CK6T245F/ref=sspa_dk_detail_3?pd_rd_i=B0CK6T245F&pd_rd_w=ben5z&content-id=amzn1.sym.9a64fe05-cdee-4d53-a27b-f3614d726545&pf_rd_p=9a64fe05-cdee-4d53-a27b-f3614d726545&pf_rd_r=83DJ4NT8B3VKXPSV5B8E&pd_rd_wg=Eou0Q&pd_rd_r=a9e726ec-70c2-46fe-974d-8f1955256835&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWxfdGhlbWF0aWM&th=1", "£259"),
    TestCase("Argos", "https://www.argos.co.uk/product/4494643?clickPR=plp:1:67", "£329"),
    TestCase("Smyths Toys", "https://www.smythstoys.com/uk/en-gb/toys/sensory-toys/physical-play-sensory-toys/5ft-smoby-life-wave-slide/p/245916", "£49.99"),
    TestCase("The Toy Shop", "https://www.thetoyshop.com/transport-toys/race-tracks/Hot-Wheels-City-T-Rex-Blaze-Battle-Playset/p/572347", "£27.99")
]


class DockerContainerTester:
    """Tests against existing Docker container"""
    
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.api_key = "test-api-key-123"
        
    def get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def test_scrape_endpoint(self, test_case: TestCase) -> Dict:
        """Test scrape endpoint against Docker container"""
        start_time = time.time()
        
        payload = {
            "url": test_case.url,
            "timeout": 30000,
            "wait_for": "load"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/scrape",
                    headers=self.get_headers(),
                    json=payload
                ) as response:
                    processing_time = int((time.time() - start_time) * 1000)
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return await self._analyze_success_response(
                            test_case, response_data, processing_time, response.status
                        )
                    else:
                        return self._create_error_result(
                            test_case, f"HTTP {response.status}: {response_data.get('detail', 'Unknown error')}", 
                            processing_time, response.status
                        )
                        
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            return self._create_error_result(
                test_case, f"Request failed: {str(e)}", processing_time, None
            )
    
    async def _analyze_success_response(self, test_case: TestCase, response_data: Dict, 
                                       processing_time: int, http_status: int) -> Dict:
        """Analyze successful response for accuracy"""
        
        # Check if scraping was successful
        if not response_data.get('success', False):
            return self._create_error_result(
                test_case, 
                response_data.get('error', 'General scraping failure'),
                processing_time, 
                http_status
            )
        
        data = response_data.get('data', {})
        actual_price = data.get('price')
        actual_currency = data.get('currency', 'USD')
        actual_title = data.get('title')
        extraction_method = response_data.get('metadata', {}).get('extraction_method', 'unknown')
        
        # Calculate price accuracy
        price_accuracy = self._calculate_price_accuracy(test_case.expected_price, actual_price)
        
        return {
            "site_name": test_case.site_name,
            "url": test_case.url,
            "expected_price": test_case.expected_price,
            "success": True,
            "actual_price": actual_price,
            "actual_currency": actual_currency,
            "actual_title": actual_title,
            "processing_time": processing_time,
            "extraction_method": extraction_method,
            "price_accuracy": price_accuracy,
            "error_message": None,
            "http_status": http_status
        }
    
    def _create_error_result(self, test_case: TestCase, error_msg: str, 
                           processing_time: int, http_status: Optional[int]) -> Dict:
        """Create standardized error result"""
        return {
            "site_name": test_case.site_name,
            "url": test_case.url,
            "expected_price": test_case.expected_price,
            "success": False,
            "actual_price": None,
            "actual_currency": None,
            "actual_title": None,
            "processing_time": processing_time,
            "extraction_method": "api-failed",
            "price_accuracy": 0.0,
            "error_message": error_msg,
            "http_status": http_status
        }
    
    def _calculate_price_accuracy(self, expected: str, actual: Optional[str]) -> float:
        """Calculate price accuracy score"""
        if not actual:
            return 0.0
        
        try:
            # Extract numeric values for comparison
            import re
            expected_num = re.findall(r'[\d.]+', expected.replace(',', ''))
            actual_num = re.findall(r'[\d.]+', str(actual).replace(',', ''))
            
            if expected_num and actual_num:
                expected_val = float(expected_num[0])
                actual_val = float(actual_num[0])
                
                # Consider prices within 5% as accurate
                if abs(expected_val - actual_val) / expected_val <= 0.05:
                    return 1.0
                else:
                    return 0.0
            return 0.0
        except:
            return 0.0


async def run_docker_integration_tests():
    """Run integration tests against Docker container"""
    print("🐳 Running Docker Integration Tests...")
    print("=" * 60)
    
    tester = DockerContainerTester()
    results = []
    total_start_time = time.time()
    
    # Test each URL
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing {test_case.site_name}...")
        result = await tester.test_scrape_endpoint(test_case)
        results.append(result)
        
        # Display result
        if result["success"]:
            accuracy_emoji = "✅" if result["price_accuracy"] > 0 else "⚠️"
            print(f"  {accuracy_emoji} Success - Price: {result['actual_price']} (Expected: {test_case.expected_price})")
            print(f"    Method: {result['extraction_method']} | Time: {result['processing_time']}ms")
        else:
            print(f"  ❌ Failed - {result['error_message']}")
    
    # Calculate summary statistics
    total_processing_time = int((time.time() - total_start_time) * 1000)
    successful_tests = [r for r in results if r["success"]]
    accuracy_scores = [r["price_accuracy"] for r in results if r["success"]]
    
    method_counts = {}
    for result in results:
        method = result["extraction_method"]
        method_counts[method] = method_counts.get(method, 0) + 1
    
    site_breakdown = {}
    for result in results:
        site = result["site_name"]
        if site not in site_breakdown:
            site_breakdown[site] = {"success": 0, "total": 0}
        site_breakdown[site]["total"] += 1
        if result["success"]:
            site_breakdown[site]["success"] += 1
    
    avg_processing_time = int(sum(r["processing_time"] for r in results) / len(results))
    
    summary = {
        "summary": {
            "total_tests": len(results),
            "successful_tests": len(successful_tests),
            "success_rate": len(successful_tests) / len(results),
            "average_processing_time": avg_processing_time,
            "price_accuracy_score": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0,
            "method_breakdown": method_counts,
            "site_breakdown": site_breakdown,
            "overall_processing_time": total_processing_time,
            "timestamp": datetime.now().isoformat(),
            "test_type": "docker_integration"
        },
        "detailed_results": results
    }
    
    # Display summary
    print("\n" + "=" * 60)
    print("📊 DOCKER INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary['summary']['total_tests']}")
    print(f"Success Rate: {summary['summary']['success_rate']:.1%} ({len(successful_tests)}/{len(results)})")
    print(f"Price Accuracy: {summary['summary']['price_accuracy_score']:.1%}")
    print(f"Average Processing Time: {avg_processing_time}ms")
    print(f"Total Test Time: {total_processing_time}ms")
    
    print(f"\nMethod Breakdown:")
    for method, count in method_counts.items():
        print(f"  {method}: {count}")
    
    print(f"\nSite Performance:")
    for site, stats in site_breakdown.items():
        success_rate = stats["success"] / stats["total"]
        print(f"  {site}: {success_rate:.1%} ({stats['success']}/{stats['total']})")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"docker_integration_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Results saved to: {filename}")
    
    return summary


if __name__ == "__main__":
    asyncio.run(run_docker_integration_tests())