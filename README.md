# 🎬 Chance Movie Bot

[![Build and Publish Docker Image](https://github.com/demjanok/chance_movie_bot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/demjanok/chance_movie_bot/actions/workflows/docker-publish.yml)
[![Docker Image](https://ghcr.io/demjanok/chance_movie_bot/badge)](https://ghcr.io/demjanok/chance_movie_bot)

A Telegram bot for discovering top-rated movie recommendations for your evening, powered by **The Movie Database (TMDB) API** and `python-telegram-bot` (v22).

## 🚀 Features
- 🎭 **Genre Selection**: Browse by popular genres (Comedy, Action, Sci-Fi, Thriller, Horror, etc.) or go with a completely random choice.
- 🌐 **Multi-Language Support (i18n)**: Seamless bilingual experience with **Ukrainian** (🇺🇦) and **English** (🇬🇧). Switch languages on the fly via `/language` or the in-menu button.
- ⭐ **Quality Filtering**: Only verified, high-rated movies (rating ≥ 7.0 and minimum 150 votes) to filter out low-quality entries.
- 🔄 **One-Click Reroll**: "Another movie" button allows instant next recommendations.
- 🛡️ **Session Deduplication**: Keeps track of recently suggested movies in a rolling buffer so you never see repetitive suggestions in a single session.
- ▶️ **Trailers & Posters**: High-resolution movie posters and direct YouTube trailer links (when available in TMDB).
- ⚡ **High Performance**: Persistent asynchronous HTTP connections and in-memory TTL caching for discover pages.
- 📊 **Structured JSON Logging**: Production-ready structured logging (JSON and human-readable text) adhering to 12-Factor App and observability best practices (compatible with Datadog, ELK, Loki, CloudWatch).
- 🐳 **Docker-ready**: Multi-stage `Dockerfile` + `docker-compose.yml` for one-command deployment anywhere Docker runs.
- 🚀 **CI/CD via GitHub Actions**: Automatic multi-platform Docker image build (`amd64` + `arm64`) and publish to `ghcr.io` on every push and semver tag; includes Trivy security scanning.

## ⚙️ Installation & Setup

### Option A — Docker (recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/demjanok/chance_movie_bot.git
   cd chance_movie_bot
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Fill in TELEGRAM_BOT_TOKEN and TMDB_API_KEY
   ```

3. **Build & start**:
   ```bash
   docker compose up -d --build
   ```

4. **View live logs**:
   ```bash
   docker compose logs -f
   ```

5. **Stop**:
   ```bash
   docker compose down
   ```

---

### Option B — Local Python

1. **Clone & enter directory**:
   ```bash
   git clone https://github.com/demjanok/chance_movie_bot.git
   cd chance_movie_bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file (you can copy `.env.example`):
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_from_botfather
   TMDB_API_KEY=your_tmdb_api_key_or_bearer_token
   MIN_RATING=7.0
   MIN_VOTES=150
   DEFAULT_LANGUAGE=uk
   MAX_DISCOVERY_PAGES=15
   SEEN_MOVIES_BUFFER_SIZE=50

   # Logging settings
   LOG_LEVEL=INFO
   LOG_FORMAT=json
   LOG_FILE=
   ```

4. **Run the bot**:
   ```bash
   python main.py
   ```

## 📱 Bot Commands
- `/start` — Start the bot and open the movie genre selection menu.
- `/help` — View usage guide and TMDB data attribution.
- `/language` (or `/lang`) — Change the interface and recommendation language.


## 🚀 CI/CD & Docker Registry

Docker images are built automatically by GitHub Actions and published to the **GitHub Container Registry (GHCR)**:

```bash
# Pull the latest image
docker pull ghcr.io/demjanok/chance_movie_bot:latest

# Pull a specific release
docker pull ghcr.io/demjanok/chance_movie_bot:1.7.0
```

### Releasing a new version

```bash
git tag v1.7.0
git push origin v1.7.0
```

This triggers the workflow and publishes:
- `ghcr.io/demjanok/chance_movie_bot:1.7.0`
- `ghcr.io/demjanok/chance_movie_bot:1.7`
- `ghcr.io/demjanok/chance_movie_bot:1`
- `ghcr.io/demjanok/chance_movie_bot:latest`
