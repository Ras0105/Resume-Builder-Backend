# backend/Dockerfile

FROM python:3.11-slim

# ---------------------------------------------------------------------------
# System dependencies Playwright's Chromium needs to actually launch headless
# in a minimal container. `playwright install --with-deps` normally handles
# this, but pinning apt packages explicitly keeps the image reproducible and
# avoids surprise breakage when Playwright's own dependency list changes.
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Install Python deps first — separate layer so `pip install` is cached
# unless requirements.txt actually changes, keeping rebuilds fast.
# ---------------------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's Chromium binary (matches the version pinned in
# requirements.txt — keep playwright's Python package and this browser
# install in sync, or page.pdf() calls can fail at runtime).
RUN playwright install chromium

# ---------------------------------------------------------------------------
# App code
# ---------------------------------------------------------------------------
COPY . .

# Run as a non-root user — Chromium in a sandboxed container behaves better
# unprivileged, and it's good practice generally for anything handling
# payment-adjacent data.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# ---------------------------------------------------------------------------
# Uvicorn as the process manager. --workers 1 is deliberate here: Playwright/
# Chromium instances are memory-heavy, and most PaaS free/starter tiers
# (Railway, Render) give you limited RAM — scale workers only once you've
# checked your plan can actually hold multiple Chromium processes at once.
# ---------------------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]