FROM python:3.11-slim

WORKDIR /app

# Install Chromium, ChromeDriver, and dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxi6 \
    libxtst6 \
    libglib2.0-0 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libxfixes3 \
    libxinerama1 \
    libpango1.0-0 \
    libatk-bridge2.0-0 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your scraper script
COPY aps_scraper.py .

# Set environment variables so Selenium knows where Chromium is
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

CMD ["python", "aps_scraper.py"]
