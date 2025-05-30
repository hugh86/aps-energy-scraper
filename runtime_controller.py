# runtime_controller.py
import time
import random
import logging
from datetime import datetime, timedelta

def wait_until_random_time(start_hour=7, start_minute=30, end_hour=7, end_minute=40):
    now = datetime.now()

    # Define today's time window
    today_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    today_end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    # If we've passed the window, wait for tomorrow
    if now > today_end:
        target_day = now + timedelta(days=1)
        today_start = target_day.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        today_end = target_day.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    # Calculate random time within window
    delta_seconds = int((today_end - today_start).total_seconds())
    random_offset = random.randint(0, delta_seconds)
    run_time = today_start + timedelta(seconds=random_offset)

    wait_seconds = max(0, (run_time - now).total_seconds())
    logging.info(f"⏳ Waiting {wait_seconds:.0f} seconds until next run at {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(wait_seconds)

    return run_time