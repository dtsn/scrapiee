# Use Python 3.11 full image (has more system libraries)
FROM python:3.11

# Set working directory
WORKDIR /app

# Install minimal system dependencies for Camoufox
RUN apt-get update && apt-get install -y \
    xvfb \
    libgtk-3-0 \
    libasound2 \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Camoufox browser
RUN python -c "import camoufox; print('Camoufox imported successfully')"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]