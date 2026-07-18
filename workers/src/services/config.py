"""Shared configuration constants for FT. THE LINE ONE API."""

# ── Free-tier usage limits ──────────────────────────────────────────
VTON_DAILY_LIMIT_FREE = 5
LLM_DAILY_LIMIT_FREE = 5
VTON_DAILY_LIMIT_PREMIUM = -1  # sentinel: unlimited
LLM_DAILY_LIMIT_PREMIUM = -1

# ── Scraper safety ─────────────────────────────────────────────────
MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP = 10
MIN_SCRAPE_COVERAGE_RATIO = 0.5
STALE_PRODUCT_THRESHOLD_HOURS = 48

# ── Image constraints ──────────────────────────────────────────────
MAX_USER_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_IMAGE_MAGIC = {
    b'\xff\xd8\xff',      # JPEG
    b'\x89PNG',           # PNG
    b'RIFF',              # WebP (RIFF container)
}

# ── Webhook security ───────────────────────────────────────────────
YOUCAM_WEBHOOK_FAIL_CLOSED = True  # reject when secret not configured
