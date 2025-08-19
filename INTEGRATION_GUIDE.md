# Scrapiee API Integration Guide

Complete guide for integrating the Scrapiee web scraping service into your applications.

## 🚀 Quick Start

### Base URL
```
https://scrapiee.onrender.com
```

### Authentication
All API requests require a Bearer token in the Authorization header:
```
Authorization: Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6
```

### Basic Usage
```bash
curl -X POST "https://scrapiee.onrender.com/api/scrape" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6" \
  -d '{"url": "https://www.johnlewis.com/product-page"}'
```

## 📚 API Reference

### POST /api/scrape
Extract product data from e-commerce websites.

**Request Body:**
```json
{
  "url": "https://example.com/product",
  "timeout": 30000,
  "wait_for": "networkidle"
}
```

**Parameters:**
- `url` (required): Target URL to scrape
- `timeout` (optional): Request timeout in ms (1000-60000, default: 30000)
- `wait_for` (optional): Page load condition
  - `networkidle`: Wait for network activity to stop (default)
  - `load`: Wait for load event
  - `domcontentloaded`: Wait for DOM ready

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "Product Name",
    "price": "29.99",
    "currency": "GBP",
    "description": "Product description...",
    "image": "https://example.com/image.jpg",
    "url": "https://example.com/product"
  },
  "metadata": {
    "timestamp": 1642608000,
    "processing_time": 3421,
    "extraction_method": "smart-selectors"
  }
}
```

### Other Endpoints
- `GET /health` - Service health check
- `GET /api/browser/status` - Browser service status (authenticated)
- `POST /api/browser/restart` - Restart browser service (authenticated)

## 🛠️ Integration Examples

### Python with requests
```python
import requests

def scrape_product(url):
    response = requests.post(
        "https://scrapiee.onrender.com/api/scrape",
        headers={
            "Authorization": "Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6",
            "Content-Type": "application/json"
        },
        json={
            "url": url,
            "timeout": 30000,
            "wait_for": "networkidle"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            return data["data"]
        else:
            print(f"Scraping failed: {data['error']['message']}")
    else:
        print(f"HTTP Error: {response.status_code}")
    
    return None

# Usage
product = scrape_product("https://www.johnlewis.com/product-page")
if product:
    print(f"Title: {product['title']}")
    print(f"Price: {product['price']} {product['currency']}")
```

### Python with httpx (async)
```python
import httpx
import asyncio

async def scrape_product_async(url):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://scrapiee.onrender.com/api/scrape",
            headers={
                "Authorization": "Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6",
                "Content-Type": "application/json"
            },
            json={
                "url": url,
                "timeout": 30000,
                "wait_for": "networkidle"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["data"] if data["success"] else None
        return None

# Usage
async def main():
    product = await scrape_product_async("https://www.johnlewis.com/product-page")
    if product:
        print(f"Title: {product['title']}")

asyncio.run(main())
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function scrapeProduct(url) {
  try {
    const response = await axios.post(
      'https://scrapiee.onrender.com/api/scrape',
      {
        url: url,
        timeout: 30000,
        wait_for: 'networkidle'
      },
      {
        headers: {
          'Authorization': 'Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6',
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.data.success) {
      return response.data.data;
    } else {
      console.error('Scraping failed:', response.data.error.message);
    }
  } catch (error) {
    console.error('Request failed:', error.message);
  }
  
  return null;
}

// Usage
scrapeProduct('https://www.johnlewis.com/product-page')
  .then(product => {
    if (product) {
      console.log(`Title: ${product.title}`);
      console.log(`Price: ${product.price} ${product.currency}`);
    }
  });
```

### JavaScript (Browser/Fetch)
```javascript
async function scrapeProduct(url) {
  try {
    const response = await fetch('https://scrapiee.onrender.com/api/scrape', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: url,
        timeout: 30000,
        wait_for: 'networkidle'
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      return data.data;
    } else {
      console.error('Scraping failed:', data.error.message);
    }
  } catch (error) {
    console.error('Request failed:', error.message);
  }
  
  return null;
}

// Usage
scrapeProduct('https://www.johnlewis.com/product-page')
  .then(product => {
    if (product) {
      document.getElementById('title').textContent = product.title;
      document.getElementById('price').textContent = `${product.price} ${product.currency}`;
    }
  });
```

### PHP
```php
<?php

function scrapeProduct($url) {
    $data = array(
        'url' => $url,
        'timeout' => 30000,
        'wait_for' => 'networkidle'
    );
    
    $options = array(
        'http' => array(
            'header' => "Content-type: application/json\r\n" .
                       "Authorization: Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6\r\n",
            'method' => 'POST',
            'content' => json_encode($data)
        )
    );
    
    $context = stream_context_create($options);
    $result = file_get_contents('https://scrapiee.onrender.com/api/scrape', false, $context);
    
    if ($result !== FALSE) {
        $response = json_decode($result, true);
        if ($response['success']) {
            return $response['data'];
        } else {
            error_log('Scraping failed: ' . $response['error']['message']);
        }
    }
    
    return null;
}

// Usage
$product = scrapeProduct('https://www.johnlewis.com/product-page');
if ($product) {
    echo "Title: " . $product['title'] . "\n";
    echo "Price: " . $product['price'] . " " . $product['currency'] . "\n";
}
?>
```

## 🔧 Advanced Usage

### Batch Processing
```python
import asyncio
import httpx

async def scrape_multiple_products(urls):
    async with httpx.AsyncClient() as client:
        tasks = []
        for url in urls:
            task = client.post(
                "https://scrapiee.onrender.com/api/scrape",
                headers={
                    "Authorization": "Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6",
                    "Content-Type": "application/json"
                },
                json={"url": url, "timeout": 30000}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        results = []
        
        for response in responses:
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    results.append(data["data"])
                else:
                    results.append(None)
            else:
                results.append(None)
        
        return results

# Usage
urls = [
    "https://www.johnlewis.com/product1",
    "https://www.amazon.co.uk/product2",
    "https://www.currys.co.uk/product3"
]

products = asyncio.run(scrape_multiple_products(urls))
for i, product in enumerate(products):
    if product:
        print(f"Product {i+1}: {product['title']} - {product['price']} {product['currency']}")
```

### Error Handling & Retry Logic
```python
import requests
import time
from typing import Optional, Dict, Any

class ScrapieClient:
    def __init__(self, api_key: str, base_url: str = "https://scrapiee.onrender.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def scrape_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/scrape",
                    json={
                        "url": url,
                        "timeout": 30000,
                        "wait_for": "networkidle"
                    },
                    timeout=120  # 2 minute timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["success"]:
                        return data["data"]
                    else:
                        error_code = data.get("error", {}).get("code", "UNKNOWN")
                        if error_code in ["BROWSER_ERROR", "TIMEOUT"]:
                            # Retry on these errors
                            if attempt < max_retries - 1:
                                print(f"Attempt {attempt + 1} failed ({error_code}), retrying...")
                                time.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        print(f"Scraping failed: {data['error']['message']}")
                        return None
                
                elif response.status_code == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        print(f"Rate limited, waiting...")
                        time.sleep(60)  # Wait 1 minute
                        continue
                
                print(f"HTTP Error: {response.status_code}")
                return None
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"Request failed ({e}), retrying...")
                    time.sleep(2 ** attempt)
                    continue
                print(f"Request failed after {max_retries} attempts: {e}")
                return None
        
        return None
    
    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False

# Usage
client = ScrapieClient("07778d5f-2b2c-41db-8f49-8583962acfe6")

if client.health_check():
    product = client.scrape_with_retry("https://www.johnlewis.com/product-page")
    if product:
        print(f"Successfully scraped: {product['title']}")
else:
    print("Service is not healthy")
```

## 🎯 Supported Websites

### Optimized Sites (Site-specific extraction rules)
- **Amazon** (amazon.com, amazon.co.uk, etc.)
- **John Lewis** (johnlewis.com)
- **Currys** (currys.co.uk)

### Generic Support
The service uses intelligent CSS selectors that work on most e-commerce sites:
- Product titles, headings, meta titles
- Current prices (excludes strikethrough/original prices)
- Product descriptions, meta descriptions
- Product images, hero images
- Auto-detected currency from symbols, codes, domain TLD

## ⚠️ Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `TIMEOUT` | Page load timeout | Retry with longer timeout |
| `DNS_ERROR` | Domain resolution failure | Check URL validity |
| `CONNECTION_REFUSED` | Server connection refused | Check if site is accessible |
| `INVALID_URL` | Malformed URL | Validate URL format |
| `BROWSER_ERROR` | Browser service issues | Retry or restart browser |
| `SCRAPING_FAILED` | General extraction failure | Check if site structure changed |

## 🚦 Rate Limits

- **10 requests per minute** per IP address
- **429 Too Many Requests** response when exceeded
- **Concurrent limit**: 2 simultaneous requests

## 🔒 Security Best Practices

1. **Store API key securely** - Use environment variables
2. **Validate URLs** - Check URLs before sending to API
3. **Handle errors gracefully** - Don't expose internal API details
4. **Implement timeouts** - Set reasonable request timeouts
5. **Monitor usage** - Track API usage and errors

## 📊 Performance Tips

1. **Use appropriate timeouts** - Faster sites can use shorter timeouts
2. **Cache results** - Store product data to avoid repeated requests
3. **Batch requests** - Process multiple URLs concurrently
4. **Monitor processing times** - Use metadata.processing_time for optimization
5. **Handle failures gracefully** - Implement retry logic for transient errors

## 🔍 Troubleshooting

### Common Issues

**Browser initialization failed:**
- Service is starting up (cold start)
- Try again in 30-60 seconds
- Use browser restart endpoint if persistent

**Empty data returned:**
- Site may have changed structure
- Try different wait_for parameter
- Check if URL is accessible

**Timeout errors:**
- Increase timeout parameter
- Site may be slow to load
- Try different wait_for condition

**Rate limit exceeded:**
- Implement exponential backoff
- Reduce request frequency
- Consider caching results

### Health Check
Always check service health before making requests:
```bash
curl https://scrapiee.onrender.com/health
```

### Browser Management
If scraping stops working, restart the browser service:
```bash
curl -X POST https://scrapiee.onrender.com/api/browser/restart \
  -H "Authorization: Bearer 07778d5f-2b2c-41db-8f49-8583962acfe6"
```

## 📝 Environment Variables

For your integration, consider these environment variables:

```bash
# .env file
SCRAPIEE_API_KEY=07778d5f-2b2c-41db-8f49-8583962acfe6
SCRAPIEE_BASE_URL=https://scrapiee.onrender.com
SCRAPIEE_TIMEOUT=30000
SCRAPIEE_MAX_RETRIES=3
```

## 📋 Testing with Postman

Import the provided Postman collection (`Scrapiee_API.postman_collection.json`) to test all endpoints interactively.

## 🆘 Support

For issues or questions:
1. Check service health: `GET /health`
2. Review error codes and messages
3. Try browser restart if needed
4. Implement retry logic for transient failures

---

*Last updated: January 2024*