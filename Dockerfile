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
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy only the requirements first to cache pip install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the project files
COPY . /app

# Add shell entrypoint that waits randomly 0–600s before executing script
ENTRYPOINT ["sh", "-c", "sleep $(( RANDOM % 601 )); exec python aps_scraper.py"]