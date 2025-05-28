FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY aps_scraper.py .

CMD ["python", "aps_scraper.py"]
