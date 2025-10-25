
# app/config.py

# Path to the SQLite database
DB_PATH = "/app/data/metrics.db"

# Folder to store downloaded YouTube videos
VIDEO_FOLDER = "/app/videos"

# Scheduler intervals (optional, for centralized tuning)
TEMP_INTERVAL_SECONDS = 60
METRICS_INTERVAL_SECONDS = 3
PRUNE_INTERVAL_HOURS = 1

TICKERS = ["INTC", "MSFT", "INFY.NS"]  # Example stock tickers