import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()

# Movie filtering configuration
MIN_RATING = float(os.getenv("MIN_RATING", "7.0"))
MIN_VOTES = int(os.getenv("MIN_VOTES", "150"))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "uk").strip()

# Maximum number of pages to sample from when picking a random movie.
#
# Calculation & Nuances:
# - TMDB API returns exactly 20 movies per page.
# - Total movie pool size = MAX_DISCOVERY_PAGES * 20.
#   * 15 pages = 300 movies (default: popular & recognizable high-rated films)
#   * 25 pages = 500 movies (more variety while keeping high recognition)
#   * 50 pages = 1000 movies (large pool, deeper cuts)
# - Note: TMDB hard caps discovery pagination at 500 pages (max 10,000 movies).
# - Higher values increase randomness/variety, but deeper pages may feature older
#   or less globally popular titles (they still meet MIN_RATING and MIN_VOTES).
MAX_DISCOVERY_PAGES = int(os.getenv("MAX_DISCOVERY_PAGES", "15"))

# Number of recently shown movie IDs to track per user session to avoid duplicates.
# A rolling buffer prevents showing recently suggested movies in a row.
SEEN_MOVIES_BUFFER_SIZE = int(os.getenv("SEEN_MOVIES_BUFFER_SIZE", "50"))

# TTL (in seconds) for the in-memory discover-page cache.
# TMDB discover results change slowly, so caching them reduces latency and API usage.
#   * 0        — disables caching entirely
#   * 600      — 10 minutes (light caching)
#   * 1200     — 20 minutes (default, good balance)
#   * 3600     — 1 hour (aggressive caching, maximizes speed)
DISCOVER_CACHE_TTL = int(os.getenv("DISCOVER_CACHE_TTL", "1200"))

# Logging configuration
# - LOG_LEVEL: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
# - LOG_FORMAT: 'json' (structured JSON logs for production/monitoring) or 'text' (human-readable)
# - LOG_FILE: optional path to write rotating logs (e.g., 'logs/bot.log')
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json").strip().lower()
LOG_FILE = os.getenv("LOG_FILE", "").strip() or None

