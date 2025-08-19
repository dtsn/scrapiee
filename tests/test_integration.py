#!/usr/bin/env python3
"""
Integration Test Suite for Scrapiee FastAPI Server
Tests the actual API endpoints against a local server to catch integration issues
"""

import asyncio
import json
import time
import aiohttp
import subprocess
import signal
import os
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

class LocalServerManager:
    """Manages local FastAPI server for testing"""
    
    def __init__(self, port: int = 8888):
        self.port = port
        self.process = None
        self.api_key = "test-api-key-123"
        
    async def start(self):
        """Start local server for testing"""
        print(f"🚀 Starting local test server on port {self.port}...")
        
        # Set environment variables for testing
        env = os.environ.copy()
        env.update({
            "PORT": str(self.port),
            "SCRAPER_API_KEY": self.api_key,
            "ENVIRONMENT": "development",
            "RATE_LIMIT_REQUESTS": "100",  # Higher limit for testing
            "RATE_LIMIT_WINDOW": "60"
        })
        
        # Start the server
        self.process = subprocess.Popen([
            "python3", "-m", "uvicorn", 
            "main:app", 
            f"--host=0.0.0.0", 
            f"--port={self.port}",
            "--log-level=warning"  # Reduce noise
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        await asyncio.sleep(3)
        
        # Check if server is running
        if self.process.poll() is not None:
            stdout, stderr = self.process.communicate()
            raise Exception(f"Failed to start server: {stderr.decode()}")
            
        print(f"✅ Test server started (PID: {self.process.pid})")
        
    async def stop(self):
        """Stop local server"""
        if self.process:
            print("🛑 Stopping test server...")
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            print("✅ Test server stopped")
    
    def get_base_url(self) -> str:
        """Get base URL for API requests"""
        return f"http://localhost:{self.port}"
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with API key"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }


class IntegrationTester:
    """Integration tester for FastAPI endpoints"""
    
    def __init__(self, server_manager: LocalServerManager):
        self.server = server_manager
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def _extract_price_value(self, price_str: str) -> float:
        """Extract numeric value from price string"""
        if not price_str:
            return 0.0
        clean_price = price_str.replace('£', '').replace('$', '').replace('€', '').replace(',', '').strip()
        try:
            return float(clean_price)
        except ValueError:
            return 0.0
    
    def _calculate_price_accuracy(self, expected: str, actual: Optional[str]) -> float:
        """Calculate price accuracy score (0-1)"""
        if not actual:
            return 0.0
        
        expected_val = self._extract_price_value(expected)
        actual_val = self._extract_price_value(actual)
        
        if expected_val == 0 or actual_val == 0:
            return 0.0
        
        diff = abs(expected_val - actual_val) / expected_val
        
        if diff == 0:
            return 1.0
        elif diff <= 0.05:
            return 0.9
        elif diff <= 0.1:
            return 0.7
        elif diff <= 0.2:
            return 0.4
        else:
            return 0.1
    
    async def test_health_endpoint(self) -> bool:
        """Test the health endpoint"""
        try:
            async with self.session.get(f"{self.server.get_base_url()}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "healthy"
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        return False
    
    async def test_scrape_endpoint(self, test_case: TestCase) -> Dict:
        """Test a single scrape endpoint"""
        start_time = time.time()
        
        try:
            print(f"🧪 Testing {test_case.site_name}: {test_case.url[:50]}...")
            
            payload = {
                "url": test_case.url,
                "timeout": 60000,
                "wait_for": "load"
            }
            
            async with self.session.post(
                f"{self.server.get_base_url()}/api/scrape",
                headers=self.server.get_headers(),
                json=payload
            ) as response:
                processing_time = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("success"):
                        product_data = data.get("data", {})
                        actual_price = product_data.get("price")
                        price_accuracy = self._calculate_price_accuracy(
                            test_case.expected_price,
                            actual_price
                        )
                        
                        result = {
                            "site_name": test_case.site_name,
                            "url": test_case.url,
                            "expected_price": test_case.expected_price,
                            "success": True,
                            "actual_price": actual_price,
                            "actual_currency": product_data.get("currency"),
                            "actual_title": product_data.get("title"),
                            "processing_time": processing_time,
                            "extraction_method": data.get("metadata", {}).get("extraction_method", "unknown"),
                            "price_accuracy": price_accuracy,
                            "error_message": None,
                            "http_status": response.status
                        }
                        
                        print(f"✅ {test_case.site_name}: Price={actual_price} (accuracy: {price_accuracy:.1%})")
                        return result
                    else:
                        error = data.get("error", {})
                        error_msg = error.get("message", "Unknown error")
                        print(f"❌ {test_case.site_name}: API Error - {error_msg}")
                        
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
                            "http_status": response.status
                        }
                else:
                    error_msg = f"HTTP {response.status}"
                    error_text = await response.text()
                    print(f"❌ {test_case.site_name}: {error_msg} - {error_text[:100]}")
                    
                    return {
                        "site_name": test_case.site_name,
                        "url": test_case.url,
                        "expected_price": test_case.expected_price,
                        "success": False,
                        "actual_price": None,
                        "actual_currency": None,
                        "actual_title": None,
                        "processing_time": processing_time,
                        "extraction_method": "http-failed",
                        "price_accuracy": 0.0,
                        "error_message": f"{error_msg}: {error_text[:100]}",
                        "http_status": response.status
                    }
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {test_case.site_name}: Exception - {error_msg[:100]}")
            
            return {
                "site_name": test_case.site_name,
                "url": test_case.url,
                "expected_price": test_case.expected_price,
                "success": False,
                "actual_price": None,
                "actual_currency": None,
                "actual_title": None,
                "processing_time": int((time.time() - start_time) * 1000),
                "extraction_method": "exception",
                "price_accuracy": 0.0,
                "error_message": error_msg[:200],
                "http_status": 0
            }
    
    async def run_all_tests(self) -> Dict:
        """Run complete integration test suite"""
        print("🧪 Starting Integration Tests against Local FastAPI Server")
        print("=" * 70)
        
        overall_start = time.time()
        
        # Test health endpoint first
        print("🏥 Testing health endpoint...")
        if not await self.test_health_endpoint():
            raise Exception("Health check failed - server not ready")
        print("✅ Health check passed")
        
        # Run scrape tests
        results = []
        for test_case in TEST_CASES:
            result = await self.test_scrape_endpoint(test_case)
            results.append(result)
            
            # Brief pause between requests
            await asyncio.sleep(1)
        
        # Calculate summary statistics
        total_tests = len(results)
        successful_tests = len([r for r in results if r["success"]])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        total_processing_time = sum(r["processing_time"] for r in results)
        average_processing_time = total_processing_time // total_tests if total_tests > 0 else 0
        
        price_accuracy_scores = [r["price_accuracy"] for r in results if r["success"]]
        price_accuracy_score = sum(price_accuracy_scores) / len(price_accuracy_scores) if price_accuracy_scores else 0
        
        # Method breakdown
        method_breakdown = {}
        for result in results:
            method = result["extraction_method"]
            method_breakdown[method] = method_breakdown.get(method, 0) + 1
        
        # Site breakdown
        site_breakdown = {}
        for result in results:
            site = result["site_name"]
            if site not in site_breakdown:
                site_breakdown[site] = {"success": 0, "total": 0}
            site_breakdown[site]["total"] += 1
            if result["success"]:
                site_breakdown[site]["success"] += 1
        
        overall_time = int((time.time() - overall_start) * 1000)
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "average_processing_time": average_processing_time,
            "price_accuracy_score": price_accuracy_score,
            "method_breakdown": method_breakdown,
            "site_breakdown": site_breakdown,
            "overall_processing_time": overall_time,
            "timestamp": datetime.now().isoformat(),
            "test_type": "integration_local_server"
        }
        
        return {
            "summary": summary,
            "detailed_results": results
        }


async def main():
    """Main integration test runner"""
    print("🧪 Scrapiee Integration Test Suite")
    print("=" * 50)
    
    server = LocalServerManager()
    
    try:
        # Start server
        await server.start()
        
        # Run tests
        async with IntegrationTester(server) as tester:
            results = await tester.run_all_tests()
            
            # Print summary
            summary = results["summary"]
            print("\n" + "=" * 70)
            print("📊 INTEGRATION TEST SUMMARY")
            print("=" * 70)
            print(f"Test Type: {summary['test_type']}")
            print(f"Total Tests: {summary['total_tests']}")
            print(f"Successful: {summary['successful_tests']} ({summary['success_rate']:.1%})")
            print(f"Average Processing Time: {summary['average_processing_time']}ms")
            print(f"Price Accuracy Score: {summary['price_accuracy_score']:.1%}")
            print(f"Overall Time: {summary['overall_processing_time']}ms")
            
            print(f"\n🔧 Method Breakdown:")
            for method, count in summary['method_breakdown'].items():
                print(f"  {method}: {count}")
            
            print(f"\n🌐 Site Success Rates:")
            for site, stats in summary['site_breakdown'].items():
                rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
                print(f"  {site}: {stats['success']}/{stats['total']} ({rate:.1%})")
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"integration_test_results_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Detailed results saved to: {filename}")
            
            # Show failures
            failures = [r for r in results["detailed_results"] if not r["success"]]
            if failures:
                print(f"\n❌ Failed Tests ({len(failures)}):")
                for failure in failures:
                    print(f"  {failure['site_name']}: {failure['error_message']}")
            
            return results
            
    except Exception as e:
        print(f"💥 Test run failed: {e}")
        return None
        
    finally:
        # Always clean up server
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())