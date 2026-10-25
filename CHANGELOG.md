# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.8] — 2026-10-25

### Added
- **Kubernetes manifests** (`k8s/`) — production-ready deployment for MicroK8s and any standard k8s cluster.
  - **`namespace.yaml`** — isolated `chance-movie-bot` namespace.
  - **`secret.yaml`** — `TELEGRAM_BOT_TOKEN` and `TMDB_API_KEY` stored as a k8s `Secret` (`stringData`); credentials are never baked into the image or ConfigMap.
  - **`configmap.yaml`** — all non-sensitive runtime variables (`MIN_RATING`, `LOG_FORMAT`, etc.) as a `ConfigMap`.
  - **`deployment.yaml`** — single-replica `Deployment` with:
    - `strategy: Recreate` — prevents two bot instances polling Telegram simultaneously (race condition guard).
    - `securityContext`: non-root user (UID 1001), `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, all Linux capabilities dropped (`drop: [ALL]`), `seccompProfile: RuntimeDefault`.
    - `livenessProbe` + `startupProbe` via exec (no HTTP port needed).
    - `readOnlyRootFilesystem` + `/tmp` `emptyDir` volume for Python/httpx temp files.
    - Resource requests/limits: 50m–500m CPU, 64Mi–256Mi RAM.
    - `terminationGracePeriodSeconds: 30` for graceful shutdown.
  - **`kustomization.yaml`** — `kustomize` entrypoint; apply everything with one command.

---

## [1.7] — 2026-10-25

### Added
- **GitHub Actions CI/CD — Build and Publish Docker Image** (`.github/workflows/docker-publish.yml`).
  - **Triggers**:
    - `push` to `master` → publishes `ghcr.io/demjanok/chance_movie_bot:latest` + `:sha-<short>`.
    - `push` of a semver tag (`v1.2.3`) → publishes `:1.2.3`, `:1.2`, `:1`, `:latest` simultaneously.
    - `pull_request` to `master` → build-only validation (no image is pushed); safely works for forks.
    - `paths-ignore` on `**.md`, `.gitignore`, `CHANGELOG.md` — docs-only commits do not trigger a rebuild.
  - **Multi-platform builds** (`linux/amd64` + `linux/arm64`) via QEMU + Docker Buildx — a single image manifest works on both cloud VPS (x86_64) and Raspberry Pi / ARM servers.
  - **GitHub Actions layer cache** (`type=gha, mode=max`) — unchanged layers are reused across runs, cutting cold-build time significantly.
  - **`docker/metadata-action`** — generates OCI-compliant image tags and labels (`org.opencontainers.image.*`) automatically from git context.
  - **Trivy security scanner** — scans the built image for CRITICAL/HIGH CVEs; results uploaded to GitHub Security → Code Scanning (SARIF); non-blocking (`continue-on-error: true`).
  - **`concurrency` guard** — in-progress runs for the same branch/PR are cancelled automatically to avoid duplicate builds and wasted runner minutes.
  - **Job summary** — a markdown summary with image name, tags, digest, platforms, and a ready-to-use `docker pull` command is posted to the GitHub Actions run page after each successful push.

---

## [1.6] — 2026-10-25

### Added
- **Docker support** — production-ready containerization with multi-stage build and non-root runtime user.
  - **`Dockerfile`** (multi-stage):
    - `builder` stage: installs Python dependencies into an isolated prefix (`/install`) using `pip install --prefix` — keeps the final image free of build tooling.
    - `runtime` stage: based on `python:3.12-slim`; copies only the installed packages and application source; runs as unprivileged user `botuser` (UID 1001) for security hardening.
    - `PYTHONUNBUFFERED=1` ensures logs stream to stdout/stderr without buffering, compatible with `docker logs` and log-collection agents.
    - `HEALTHCHECK` verifies the Python process is alive every 30 seconds.
  - **`docker-compose.yml`**:
    - Single `bot` service with `restart: unless-stopped` for automatic crash recovery.
    - `env_file: .env` — secrets are never baked into the image; the `.env` file is loaded at runtime.
    - Named volume `bot_logs` mounted at `/app/logs` for optional persistent file logging (activated via `LOG_FILE=logs/bot.log`).
    - Docker `json-file` logging driver with 10 MB rotation and 5 backup files, aligning with the app-level `JSONFormatter` output.
    - Resource limits: CPU 0.5 cores / 256 MB RAM (reservations: 0.1 CPU / 64 MB).
  - **`.dockerignore`**: excludes `.env`, `.venv`, `.git`, `*.log`, test files, docs, and Docker files themselves to keep the build context minimal and prevent secret leakage.
  - **`.gitignore`** updated: added `logs/` and `*.log` exclusions.

### Changed
- **`README.md`** — added **Option A (Docker)** as the recommended deployment path with full `docker compose` instructions; the existing local Python setup moved to **Option B**.

---

## [1.5] — 2026-10-19

### Added
- **Structured JSON Logging** (`logging_config.py`) — production-ready logging according to 12-Factor App and cloud observability standards (compatible with Datadog, ELK, Grafana Loki, AWS CloudWatch).
  - Custom `JSONFormatter` producing single-line JSON records (NDJSON) with standard fields: `timestamp` (UTC ISO 8601), `level`, `service`, `logger`, `message`, `module`, `function`, `line`.
  - Structured exception serialization capturing exception type, message, and formatted traceback.
  - Automatic extraction and merging of contextual attributes passed via `extra={...}` into top-level JSON fields.
  - Full Unicode and emoji support with automatic UTF-8 stream reconfiguration for Windows and Linux environments.
  - Optional `RotatingFileHandler` support (10MB limit, 5 backup files) with automatic directory creation.
- **Configurable Logging Environment Variables** (`config.py`, `.env.example`):
  - `LOG_LEVEL` (default: `INFO`) — controls log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
  - `LOG_FORMAT` (default: `json`) — toggle between machine-readable `json` and human-readable `text`.
  - `LOG_FILE` (optional) — path to rotating log file.
- **Third-Party Noise Suppression** (`logging_config.py`) — throttled chatty polling and connection loggers (`httpx`, `httpcore`, `telegram`, `asyncio`, etc.) to `WARNING` by default to preserve a high signal-to-noise ratio.
- **Structured Context Across All Handlers**:
  - Global `error_handler` logs unhandled exceptions enriched with `user_id`, `chat_id`, and `update_id`.
  - `start.py` logs `/start`, `/help`, and language changes with user context.
  - `movies.py` logs recommendation requests and results with `user_id`, `genre_id`, `movie_id`, and `lang`.
  - `tmdb_service.py` logs cache hits, HTTP errors, and details retrieval with structured parameters.
- **Comprehensive Unit Test Suite** (`test_logging.py`) — automated verification of JSON formatting, Unicode/emoji safety, contextual fields, exception serialization, file rotation, and third-party logger quieting.

---

## [1.4] — 2026-10-18

### Added
- **Multi-language localization (i18n)** (`locales.py`) — full internationalization supporting Ukrainian (`uk`) and English (`en`).
  - Added centralized translation catalogs for all user-facing strings, buttons, genre names, and movie card formatting.
  - Added automatic user language detection from Telegram client settings (`language_code`), with fallback to `DEFAULT_LANGUAGE` (`uk`).
  - Added `/language` and `/lang` commands alongside an interactive language selector inline keyboard (`get_language_keyboard`).
  - Added "🌐 Language / Мова" button in the genre selection menu for quick language switching.
  - Added dynamic TMDB API localized querying (`uk-UA` and `en-US`), fetching titles, overviews, and genres in the user's active language.
  - Multi-language cache isolation: discovery cache keys now partition by language (`{lang}:{genre_id}:{page}`).
- **Configurable `DEFAULT_LANGUAGE`** (`config.py`, `.env.example`) — new environment variable to set the default interface language.

### Changed
- **Full documentation and codebase translated to English** — translated `README.md` and ensured all comments, docstrings, and log messages across all modules are written in English.
- **Dynamic localized handlers** — updated `handlers/start.py`, `handlers/movies.py`, `keyboards.py`, and `main.py` to adapt dynamically to the user's chosen language.

---

## [1.3] — 2026-10-18

### Performance
- **Persistent `AsyncClient`** (`tmdb_service.py`) — replaced `async with httpx.AsyncClient(...)` inside every
  method with a shared `self._client` instance reused across requests. Eliminates redundant
  TCP handshakes on every user interaction. Added `close()` coroutine called on bot shutdown
  via `post_shutdown` hook in `main.py`.
- **In-memory TTL cache for discover pages** (`tmdb_service.py`) — TMDB `/discover/movie`
  responses are cached per `(genre_id, page)` key for 20 minutes. Repeated "Another movie"
  clicks within the TTL window skip the network round-trip entirely.
- **Parallel HTTP requests via `asyncio.gather`** (`tmdb_service.py`) — `get_movie_details()`
  now fetches Ukrainian and English metadata **concurrently**. Also falls back to English
  video list when Ukrainian `videos.results` is empty.
- **Concurrent discover page fetching** (`tmdb_service.py`) — up to 3 random discover pages
  are now fetched in parallel via `asyncio.gather` instead of sequentially.

### Added
- **Global `error_handler`** (`main.py`) — unhandled exceptions are now logged with full
  traceback and the user receives a Telegram alert instead of silence or a hanging spinner.
- **`ANY_GENRE` constant** (`tmdb_service.py`) — replaces the magic string `"any"` in genre
  filtering, `POPULAR_GENRES` dict key, and keyboard generation.

### Changed
- **`deque` for `seen_movies` buffer** (`handlers/movies.py`) — replaced `list` + `pop(0)`
  (O(n)) with `collections.deque(maxlen=SEEN_MOVIES_BUFFER_SIZE)` (O(1) append/evict).
  Manual length-check and `pop(0)` removed; `deque` enforces the cap automatically.
- **Dynamic rating in welcome text** (`handlers/start.py`) — hardcoded `"7.0"` replaced
  with `config.MIN_RATING` so the message stays in sync with the env variable.
- **`ANY_GENRE` constant in keyboards** (`keyboards.py`) — string literal `"any"` replaced
  with the imported `ANY_GENRE` constant.
- **Removed redundant `asyncio` event-loop workaround** (`main.py`) — the `try/except RuntimeError`
  block for manually creating an event loop is no longer needed; `python-telegram-bot` v22
  manages its own loop via `app.run_polling()`.

---

## [1.2] — 2026-10-18

### Added
- **`seen_movies` deduplication buffer** (`handlers/movies.py`, `config.py`) — the bot now
  tracks recently shown movie IDs per user session in a rolling buffer to avoid recommending
  the same movie twice in a row. Buffer size is configurable via `SEEN_MOVIES_BUFFER_SIZE`
  env variable (default: 50).
- **`SEEN_MOVIES_BUFFER_SIZE` config option** (`config.py`, `.env.example`) — new env
  variable to control the deduplication window.

### Changed
- **`get_random_movie()` now accepts `exclude_ids`** (`tmdb_service.py`) — the method
  samples up to 3 random pages and filters out previously seen movies. Falls back to any
  movie from the initial page if all sampled results were already seen.
- **Discovery page sampling** (`tmdb_service.py`) — instead of picking a single random page,
  now samples up to 3 pages (`random.sample`) and picks the first one containing unseen movies.
- **`requirements.txt`** — pinned version range tightened.

---

## [1.1] — 2026-10-14

### Changed
- **Codebase localization to English** — all Ukrainian-language comments, log messages,
  and docstrings translated to English for consistency.
- **`MAX_DISCOVERY_PAGES` made configurable** (`config.py`, `tmdb_service.py`) — replaced
  the hardcoded value of `15` with `config.MAX_DISCOVERY_PAGES` (env variable, default: 15).
  Added detailed comment explaining the page/movie pool math and TMDB's 500-page hard cap.
- **Refactored handlers and keyboards** — improved docstrings, code style, and English
  comments across `handlers/movies.py`, `handlers/start.py`, `keyboards.py`.
- **`menu_genres_callback`** (`handlers/movies.py`) — extracted into a dedicated function
  (was previously inline or missing), handles "Back to genres" button clicks.

### Added
- **`/help` command** (`handlers/start.py`) — displays usage instructions and TMDB attribution.

---

## [1.0] — 2026-10-14

### Added
- **Full bot rewrite** replacing the bare prototype with a production-ready structure:
  - `config.py` — centralized configuration via `.env` / environment variables
    (`TELEGRAM_BOT_TOKEN`, `TMDB_API_KEY`, `MIN_RATING`, `MIN_VOTES`, `MAX_DISCOVERY_PAGES`).
  - `services/tmdb_service.py` — `TMDBService` class with TMDB Discover API integration,
    dual auth support (API Key v3 and Bearer JWT v4), rating/vote filtering, random page
    sampling, Ukrainian locale with English overview fallback, and YouTube trailer lookup.
  - `handlers/movies.py` — `movie_callback_handler` (genre selection + "Another movie"),
    `format_movie_caption()` with HTML formatting and 1024-char Telegram caption guard.
  - `handlers/start.py` — `/start` and `/help` command handlers with inline genre keyboard.
  - `keyboards.py` — `get_genres_keyboard()` and `get_movie_actions_keyboard()`.
  - `README.md` — setup instructions and feature overview.
  - `.env.example` — template for required environment variables.
- **TMDB API integration** — replaces the previous OMDb integration.
- **Inline keyboard UI** — genre selection grid + "Another movie" / "Trailer" / "Back" buttons.
- **Poster display** — sends movie poster via `reply_photo`; falls back to text if unavailable.
- **Startup validation** — checks for missing `TELEGRAM_BOT_TOKEN` / `TMDB_API_KEY` and
  logs actionable error messages.
- **`python-telegram-bot` v22** — `CallbackQueryHandler`, `ApplicationBuilder`, async handlers.

### Changed
- **`main.py`** — restructured into a `main()` function with proper handler registration,
  logging setup, and asyncio event-loop compatibility note for Python 3.14+.
- **`requirements.txt`** — added `httpx` and `python-dotenv`; updated `python-telegram-bot`
  to `>=22.0,<23.0`.

---

## [0.2] — 2025-05-06 *(initial commit — OMDb experiment)*

### Added
- `get_movie()` function using the **OMDb API** to fetch a hardcoded movie ("Inception")
  and print its IMDb rating if above 3.0. Called synchronously on startup before the bot loop.

### Notes
- Bot token was stored as a plain string literal in source — not yet moved to env variables.
- OMDb integration was exploratory and not wired into any Telegram handler.

---

## [0.1] — 2025-04-29 *(initial commit — skeleton)*

### Added
- Minimal Telegram bot skeleton with a single `/start` command replying `"I'm alive!😎"`.
- `requirements.txt` with `python-telegram-bot==22.0`.
- `.gitignore` for Python project (added in a separate commit).

---

[Unreleased]: https://github.com/demjanok/chance_movie_bot/compare/1.4...HEAD
[1.4]: https://github.com/demjanok/chance_movie_bot/compare/1.3...1.4
[1.3]: https://github.com/demjanok/chance_movie_bot/compare/1.2...1.3
[1.2]: https://github.com/demjanok/chance_movie_bot/compare/1.1...1.2
[1.1]: https://github.com/demjanok/chance_movie_bot/compare/1.0...1.1
[1.0]: https://github.com/demjanok/chance_movie_bot/compare/0.2...1.0
[0.2]: https://github.com/demjanok/chance_movie_bot/compare/0.1...0.2
[0.1]: https://github.com/demjanok/chance_movie_bot/releases/tag/0.1
