FROM arm64v8/python:3.11-slim

# Install system and Chrome dependencies
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
    chromium \
    chromium-driver && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chromium and Chromedriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/lib/chromium/chromedriver

# Set working directory
WORKDIR /app

# Copy all project files (including .env if used for dev, but you can exclude it with .dockerignore)
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the scraper
CMD ["python", "aps_scraper.py"]
