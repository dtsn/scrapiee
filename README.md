# Scrapiee - FastAPI Web Scraping Service

A modern, high-performance web scraping API built with FastAPI and Camoufox, designed for extracting product data from e-commerce websites.

## 🚀 Features

- **⚡ FastAPI Framework**: Modern, fast, with automatic API documentation
- **🦊 Camoufox Integration**: Python-native anti-detection browser automation
- **🔐 Secure Authentication**: API key authentication with rate limiting
- **🎯 Smart Data Extraction**: Intelligent element detection for product information
- **📊 Structured Responses**: Clean JSON with comprehensive metadata
- **☁️ Cloud Ready**: Optimized for Render.com deployment
- **📖 Auto Documentation**: Interactive API docs at `/docs`

## 📋 API Reference

### Authentication
All requests require a Bearer token in the `Authorization` header:
```
Authorization: Bearer your-api-key-here
```

### Endpoints

#### `POST /api/scrape`
Extract product data from a URL.

**Request:**
```json
{
  "url": "https://example.com/product",
  "timeout": 30000,
  "wait_for": "networkidle"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "title": "Product Name",
    "price": "29.99",
    "currency": "USD", 
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

#### `GET /health`
Service health check.

#### `GET /api/browser/status`
Browser service status (authenticated).

#### `POST /api/browser/restart`
Restart browser service (authenticated).

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- pip or poetry

### Setup
```bash
# Clone repository
git clone <repository-url>
cd scrapiee

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API key

# Start development server
python main.py
```

The API will be available at `http://localhost:8000` with interactive documentation at `/docs`.

### Project Structure
```
scrapiee/
├── app/
│   ├── __init__.py
│   ├── models.py              # Pydantic models for requests/responses
│   └── services/
│       ├── __init__.py
│       ├── browser_service.py # Camoufox browser management
│       ├── extractor_service.py # Data extraction logic
│       └── scraper_service.py # Main scraping orchestration
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── render.yaml               # Render.com deployment config
├── .env                      # Environment variables (local)
├── .gitignore               # Git ignore patterns
└── README.md                # Project documentation
```

## 📡 Usage Examples

### cURL
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "url": "https://www.johnlewis.com/ninja-af180-max-pro-air-fryer-black/p111501862",
    "timeout": 30000,
    "wait_for": "networkidle"
  }'
```

### Python
```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/scrape",
    headers={"Authorization": "Bearer your-api-key"},
    json={
        "url": "https://example.com/product",
        "timeout": 30000,
        "wait_for": "networkidle"
    }
)
data = response.json()
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/scrape', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-api-key'
  },
  body: JSON.stringify({
    url: 'https://example.com/product',
    timeout: 30000,
    wait_for: 'networkidle'
  })
});
const data = await response.json();
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────────────────────┐ │
│  │  Authentication │    │        Rate Limiting             │ │
│  │  & Validation   │    │        & CORS                    │ │
│  └─────────────────┘    └──────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────────────────────┐ │
│  │ Scraper Service │    │      Browser Service             │ │
│  │                 │    │                                  │ │
│  │ • Request       │    │ • Camoufox Management           │ │
│  │   Orchestration │    │ • Page Lifecycle                │ │
│  │ • Error         │    │ • Resource Optimization         │ │
│  │   Handling      │    │ • Concurrent Request Limiting   │ │
│  └─────────────────┘    └──────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Extractor Service                          │ │
│  │                                                         │ │
│  │ • Smart Element Detection                               │ │
│  │ • Currency Recognition                                  │ │
│  │ • Data Cleaning & Validation                           │ │
│  │ • BeautifulSoup HTML Parsing                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment

### Render.com
1. Connect your GitHub repository
2. The `render.yaml` will automatically configure deployment
3. API key will be auto-generated
4. Service will be available at `https://your-app.onrender.com`

### Docker
```bash
# Build image
docker build -t scrapiee .

# Run container
docker run -p 8000:8000 -e SCRAPER_API_KEY=your-key scrapiee
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPER_API_KEY` | - | API authentication key |
| `PORT` | 8000 | Server port |
| `ENVIRONMENT` | development | Environment mode |
| `BROWSER_TIMEOUT` | 30000 | Browser timeout (ms) |
| `MAX_CONCURRENT_REQUESTS` | 2 | Max concurrent scraping |
| `RATE_LIMIT_REQUESTS` | 10 | Requests per time window |
| `RATE_LIMIT_WINDOW` | 60 | Rate limit window (seconds) |

### Request Parameters

- `url` (required): Target URL to scrape
- `timeout` (optional): Request timeout (1000-60000ms, default: 30000)
- `wait_for` (optional): Page load condition
  - `networkidle`: Wait for network activity to stop (default)
  - `load`: Wait for load event
  - `domcontentloaded`: Wait for DOM to be ready

## 🔍 Data Extraction

The service uses intelligent CSS selectors to extract:

- **Title**: Product titles, headings, meta titles
- **Price**: Current prices (excludes strikethrough/original prices) 
- **Description**: Product descriptions, meta descriptions
- **Image**: Product images, hero images, gallery images
- **Currency**: Auto-detected from symbols, codes, domain TLD

## 🛡️ Security & Rate Limiting

- **Authentication**: Bearer token required for all scraping endpoints
- **Rate Limiting**: 10 requests per minute per IP (configurable)
- **CORS**: Configurable origins for web applications
- **Input Validation**: Pydantic models with comprehensive validation
- **Error Handling**: Secure error responses without internal details

## 📊 Performance

- **Concurrent Requests**: Limited to 2 simultaneous scraping operations
- **Resource Optimization**: Images/CSS/fonts blocked for faster loading
- **Smart Timeouts**: Fallback loading strategies for difficult sites
- **Memory Management**: Automatic page cleanup and browser restart

## 🐛 Error Handling

Comprehensive error classification:
- `TIMEOUT`: Page load timeout
- `DNS_ERROR`: Domain resolution failure  
- `CONNECTION_REFUSED`: Server connection refused
- `INVALID_URL`: Malformed URL
- `BROWSER_ERROR`: Browser service issues
- `SCRAPING_FAILED`: General extraction failure

## 📜 License

MIT License - see LICENSE file for details.