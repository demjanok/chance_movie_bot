# ============================================================
# Stage 1: dependency builder
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install pip dependencies into an isolated prefix so we can
# copy only the wheel-installed packages to the runtime stage
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ============================================================
# Stage 2: lean runtime image
# ============================================================
FROM python:3.12-slim AS runtime

# ── OS hardening ─────────────────────────────────────────────
# Create a non-root user so the process never runs as root.
RUN groupadd --gid 1001 botuser \
 && useradd  --uid 1001 --gid botuser --no-create-home --shell /sbin/nologin botuser

# ── Python path: copy installed packages from builder ────────
COPY --from=builder /install /usr/local

# ── Application source ───────────────────────────────────────
WORKDIR /app
COPY --chown=botuser:botuser . .

# ── Runtime environment defaults ─────────────────────────────
# All values can be overridden at container runtime via
#   docker run -e LOG_LEVEL=DEBUG ...  or  docker-compose.yml.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=UTF-8 \
    LOG_FORMAT=json \
    LOG_LEVEL=INFO \
    LOG_FILE=""

# Drop to non-root user
USER botuser

# ── Health-check (no TCP port; verify process is alive) ──────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["python", "-u", "main.py"]

