FROM arm64v8/python:3.11-slim

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    xdg-utils \
    fonts-liberation \
    libu2f-udev \
    ca-certificates \
    wget \
    chromium \
    chromium-driver && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables to use Chromium and its driver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/lib/chromium/chromedriver

# Set up the working directory
WORKDIR /app

# Copy app files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the scraper
CMD ["python", "aps_scraper.py"]
