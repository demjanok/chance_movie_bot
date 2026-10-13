import os
from pathlib import Path
from dotenv import load_dotenv

# Завантажуємо змінні з .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()

# Налаштування фільтрації фільмів
MIN_RATING = float(os.getenv("MIN_RATING", "7.0"))
MIN_VOTES = int(os.getenv("MIN_VOTES", "150"))
TMDB_LANGUAGE = "uk-UA"
