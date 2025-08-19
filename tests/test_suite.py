"""
Comprehensive Test Suite for Scrapiee Scraping Performance
Tests scraping accuracy and success rates across multiple UK e-commerce sites
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper_service_v2 import ScraperServiceV2


@dataclass
class TestCase:
    """Test case definition"""
    url: str
    expected_price: str
    expected_currency: str = "GBP"
    site_name: str = ""
    category: str = ""


@dataclass
class TestResult:
    """Individual test result"""
    test_case: TestCase
    success: bool
    actual_price: Optional[str]
    actual_currency: Optional[str] 
    actual_title: Optional[str]
    actual_description: Optional[str]
    actual_image: Optional[str]
    processing_time: int
    extraction_method: str
    error_message: Optional[str] = None
    price_accuracy: float = 0.0  # 0-1 score for price accuracy


@dataclass 
class TestSummary:
    """Overall test suite summary"""
    total_tests: int
    successful_tests: int
    success_rate: float
    average_processing_time: int
    price_accuracy_score: float
    method_breakdown: Dict[str, int]
    site_breakdown: Dict[str, Dict[str, int]]
    timestamp: str


class ScrapingTestSuite:
    """Comprehensive testing suite for scraping performance"""
    
    # Test cases from examples.md with expected outcomes
    TEST_CASES = [
        TestCase(
            url="https://www.halfords.com/bikes/hybrid-bikes/boardman-mtx-8.6-mens-hybrid-bike-2021---s-m-l-frames-366006.html",
            expected_price="£600",
            site_name="Halfords",
            category="Bikes"
        ),
        TestCase(
            url="https://www.decathlon.co.uk/p/4-man-inflatable-blackout-tent-air-seconds-4-1/_/R-p-302837?mc=8648382&c=cappuccino%20beige",
            expected_price="£299.99", 
            site_name="Decathlon",
            category="Sports"
        ),
        TestCase(
            url="https://www.johnlewis.com/john-lewis-handheld-foldable-desk-fan-4-inch/white/p5873998",
            expected_price="£12",
            site_name="John Lewis",
            category="Home"
        ),
        TestCase(
            url="https://www.amazon.co.uk/dp/B0CK6T245F/ref=sspa_dk_detail_3?pd_rd_i=B0CK6T245F&pd_rd_w=ben5z&content-id=amzn1.sym.9a64fe05-cdee-4d53-a27b-f3614d726545&pf_rd_p=9a64fe05-cdee-4d53-a27b-f3614d726545&pf_rd_r=83DJ4NT8B3VKXPSV5B8E&pd_rd_wg=Eou0Q&pd_rd_r=a9e726ec-70c2-46fe-974d-8f1955256835&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWxfdGhlbWF0aWM&th=1",
            expected_price="£259",
            site_name="Amazon UK", 
            category="Electronics"
        ),
        TestCase(
            url="https://www.argos.co.uk/product/4494643?clickPR=plp:1:67",
            expected_price="£329",
            site_name="Argos",
            category="Electronics"
        ),
        TestCase(
            url="https://www.smythstoys.com/uk/en-gb/toys/sensory-toys/physical-play-sensory-toys/5ft-smoby-life-wave-slide/p/245916",
            expected_price="£49.99",
            site_name="Smyths Toys",
            category="Toys"
        ),
        TestCase(
            url="https://www.thetoyshop.com/transport-toys/race-tracks/Hot-Wheels-City-T-Rex-Blaze-Battle-Playset/p/572347",
            expected_price="£27.99",
            site_name="The Toy Shop",
            category="Toys"
        )
    ]
    
    def __init__(self):
        self.scraper = ScraperServiceV2()
        self.results: List[TestResult] = []
    
    def _extract_price_value(self, price_str: str) -> float:
        """Extract numeric value from price string"""
        if not price_str:
            return 0.0
        
        # Remove currency symbols and extract number
        cleaned = re.sub(r'[£$€¥₹,]', '', price_str.strip())
        match = re.search(r'(\d+\.?\d*)', cleaned)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        return 0.0
    
    def _calculate_price_accuracy(self, expected: str, actual: Optional[str]) -> float:
        """Calculate price accuracy score (0-1)"""
        if not actual:
            return 0.0
        
        expected_val = self._extract_price_value(expected)
        actual_val = self._extract_price_value(actual)
        
        if expected_val == 0 or actual_val == 0:
            return 0.0
        
        # Calculate percentage difference
        diff = abs(expected_val - actual_val) / expected_val
        
        # Score: 1.0 for exact match, decreasing with difference
        if diff == 0:
            return 1.0
        elif diff <= 0.05:  # Within 5%
            return 0.9
        elif diff <= 0.1:   # Within 10%
            return 0.7
        elif diff <= 0.2:   # Within 20%
            return 0.5
        elif diff <= 0.5:   # Within 50%
            return 0.3
        else:
            return 0.1
    
    async def run_single_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case"""
        print(f"🧪 Testing {test_case.site_name}: {test_case.expected_price}")
        print(f"   URL: {test_case.url[:60]}...")
        
        start_time = time.time()
        
        try:
            result = await self.scraper.scrape_url(test_case.url, timeout=30000)
            
            success = result.get('success', False)
            data = result.get('data', {}) if success else {}
            metadata = result.get('metadata', {})
            error = result.get('error') if not success else None
            
            # Calculate price accuracy
            price_accuracy = self._calculate_price_accuracy(
                test_case.expected_price, 
                data.get('price') if success else None
            )
            
            test_result = TestResult(
                test_case=test_case,
                success=success,
                actual_price=data.get('price') if success else None,
                actual_currency=data.get('currency') if success else None,
                actual_title=data.get('title') if success else None,
                actual_description=data.get('description') if success else None,
                actual_image=data.get('image') if success else None,
                processing_time=metadata.get('processing_time', 0),
                extraction_method=metadata.get('extraction_method', 'unknown'),
                error_message=error.get('message') if error else None,
                price_accuracy=price_accuracy
            )
            
            # Print result summary
            if success:
                print(f"   ✅ Success ({test_result.processing_time}ms)")
                print(f"   💰 Price: {data.get('price')} (expected {test_case.expected_price})")
                print(f"   📊 Accuracy: {price_accuracy:.2f}")
                print(f"   🔧 Method: {test_result.extraction_method}")
            else:
                print(f"   ❌ Failed: {error.get('message', 'Unknown error') if error else 'No error info'}")
            
            return test_result
            
        except Exception as e:
            print(f"   💥 Exception: {str(e)[:100]}")
            return TestResult(
                test_case=test_case,
                success=False,
                actual_price=None,
                actual_currency=None,
                actual_title=None,
                actual_description=None,
                actual_image=None,
                processing_time=int((time.time() - start_time) * 1000),
                extraction_method='exception',
                error_message=str(e),
                price_accuracy=0.0
            )
    
    async def run_all_tests(self, max_concurrent: int = 1) -> TestSummary:
        """Run all test cases"""
        print("🚀 Starting Scrapiee Test Suite")
        print(f"📋 Testing {len(self.TEST_CASES)} URLs across {len(set(tc.site_name for tc in self.TEST_CASES))} sites")
        print("-" * 80)
        
        # Run tests (sequentially for now to avoid overwhelming sites)
        self.results = []
        for i, test_case in enumerate(self.TEST_CASES, 1):
            print(f"\n[{i}/{len(self.TEST_CASES)}]", end=" ")
            result = await self.run_single_test(test_case)
            self.results.append(result)
            
            # Small delay between tests
            if i < len(self.TEST_CASES):
                print("   ⏳ Waiting 2s...")
                await asyncio.sleep(2)
        
        # Generate summary
        summary = self._generate_summary()
        
        print("\n" + "=" * 80)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 80)
        self._print_summary(summary)
        
        return summary
    
    def _generate_summary(self) -> TestSummary:
        """Generate test suite summary"""
        successful = [r for r in self.results if r.success]
        
        # Calculate metrics
        success_rate = len(successful) / len(self.results) if self.results else 0
        avg_time = sum(r.processing_time for r in successful) // len(successful) if successful else 0
        price_accuracy = sum(r.price_accuracy for r in self.results) / len(self.results) if self.results else 0
        
        # Method breakdown
        method_breakdown = {}
        for result in successful:
            method = result.extraction_method
            method_breakdown[method] = method_breakdown.get(method, 0) + 1
        
        # Site breakdown
        site_breakdown = {}
        for result in self.results:
            site = result.test_case.site_name
            if site not in site_breakdown:
                site_breakdown[site] = {'success': 0, 'total': 0}
            
            site_breakdown[site]['total'] += 1
            if result.success:
                site_breakdown[site]['success'] += 1
        
        return TestSummary(
            total_tests=len(self.results),
            successful_tests=len(successful),
            success_rate=success_rate,
            average_processing_time=avg_time,
            price_accuracy_score=price_accuracy,
            method_breakdown=method_breakdown,
            site_breakdown=site_breakdown,
            timestamp=datetime.now().isoformat()
        )
    
    def _print_summary(self, summary: TestSummary):
        """Print formatted test summary"""
        print(f"🎯 Overall Success Rate: {summary.success_rate:.1%} ({summary.successful_tests}/{summary.total_tests})")
        print(f"⚡ Average Processing Time: {summary.average_processing_time}ms")
        print(f"💰 Price Accuracy Score: {summary.price_accuracy_score:.2f}/1.0")
        
        print(f"\n📊 Method Breakdown:")
        for method, count in summary.method_breakdown.items():
            print(f"   {method}: {count} sites")
        
        print(f"\n🏪 Site Performance:")
        for site, stats in summary.site_breakdown.items():
            rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0
            status = "✅" if rate > 0.8 else "⚠️" if rate > 0.5 else "❌"
            print(f"   {status} {site}: {rate:.1%} ({stats['success']}/{stats['total']})")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for i, result in enumerate(self.results, 1):
            status = "✅" if result.success else "❌"
            accuracy = f"({result.price_accuracy:.2f})" if result.success else ""
            time_info = f"{result.processing_time}ms" if result.success else "N/A"
            
            print(f"   {status} [{i}] {result.test_case.site_name}: {time_info} {accuracy}")
            if result.success:
                print(f"       Price: {result.actual_price} (expected {result.test_case.expected_price})")
            else:
                print(f"       Error: {result.error_message}")
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        summary = self._generate_summary()
        
        data = {
            'summary': {
                'total_tests': summary.total_tests,
                'successful_tests': summary.successful_tests,
                'success_rate': summary.success_rate,
                'average_processing_time': summary.average_processing_time,
                'price_accuracy_score': summary.price_accuracy_score,
                'method_breakdown': summary.method_breakdown,
                'site_breakdown': summary.site_breakdown,
                'timestamp': summary.timestamp
            },
            'detailed_results': [
                {
                    'site_name': r.test_case.site_name,
                    'url': r.test_case.url,
                    'expected_price': r.test_case.expected_price,
                    'success': r.success,
                    'actual_price': r.actual_price,
                    'actual_currency': r.actual_currency,
                    'processing_time': r.processing_time,
                    'extraction_method': r.extraction_method,
                    'price_accuracy': r.price_accuracy,
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
    
    async def close(self):
        """Clean up resources"""
        await self.scraper.close()


async def main():
    """Main test runner"""
    test_suite = ScrapingTestSuite()
    
    try:
        summary = await test_suite.run_all_tests()
        test_suite.save_results()
        
        # Return summary for programmatic use
        return summary
        
    finally:
        await test_suite.close()


if __name__ == "__main__":
    asyncio.run(main())