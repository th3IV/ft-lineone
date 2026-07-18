# FT-LineOne — AI Agent Context

> Single source of truth for any AI agent working on this project.

## Project Overview

**ft-lineone** is a fashion e-commerce platform with Virtual Try-On (VTON), LLM-powered recommendations, and a Freemium/Premium subscription model via Transbank WebPay.

- **Domain**: `thelineone.com` (Pages frontend + Workers API on same domain)
- **Branch**: `feat/cloudflare-migration`
- **Backup branches**: `cloudflare-respaldo` (7e63910), `backup-antes-freemium` (7f2ed13)

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Redux Toolkit + React Router v6 + Tailwind CSS + Framer Motion |
| API | Cloudflare Workers (Python) + FastAPI + Pydantic |
| Database | Cloudflare D1 (`ft-lineone-db`) |
| Storage | Cloudflare R2 (`r2-thelineone01`) |
| LLM | Cloudflare Workers AI — `@cf/meta/llama-3.3-70b-instruct-fp8-fast` |
| VTON | YouCam API V3.0 (`yce-api-01.makeupar.com`) |
| Payments | Transbank WebPay Plus REST API v1.2 |
| Cron | `*/45 * * * *` (scrapers + VTON polling + cleanup) |

## Cloudflare Bindings

| Binding | Type | Name |
|---------|------|------|
| `DB` | D1 | `ft-lineone-db` (95835a2d-02ce-48bb-a53d-a89636f1508c) |
| `R2` | R2 | `r2-thelineone01` |
| `AI` | Workers AI | (unnamed) |

## Wrangler Secrets

- `JWT_SECRET` — HMAC-SHA256 signing key
- `REPLICATE_API_TOKEN` — Replicate API (unused, legacy)
- `TRANSBANK_API_KEY` — Transbank API secret
- `YOUCAM_API_KEY` — YouCam Bearer token
- `YOUCAM_WEBHOOK_SECRET` — YouCam webhook HMAC secret

## Wrangler Vars (non-secret)

- `JWT_ALGORITHM`: `HS256`
- `CORS_ORIGINS`: `thelineone.com`, `www.thelineone.com`, `localhost:3000`, `feat-cloudflare-migration.ft-lineone.pages.dev`
- `CLOUDFLARE_AI_GATEWAY_ID`: `ft-lineone-vton`
- `TRANSBANK_COMMERCE_CODE`: `597055555532` (integration/sandbox)
- `TRANSBANK_BASE_URL`: `https://webpay3gint.transbank.cl`
- `TRANSBANK_RETURN_URL`: `https://thelineone.com/payment/success`

**Wrangler flags**: `["python_workers", "disable_python_no_global_handlers"]` — NOT `nodejs_compat`.

## Workers Python Gotchas

- `os.getenv()` does NOT work at import time. Secrets only arrive via `self.env` binding.
- `Response()` uses `status=`, NOT `status_code=`.
- `time.time_ns()` is NOT available in Pyodide. Use `str(time.time()).encode()`.
- R2 uploads must use `import js` + `to_js()` from `pyodide.ffi` with `Object.fromEntries` dict_converter.
- `app.state` is set per-request in `on_fetch` (lines 239-240 of entry.py).

## Database Schema

Tables: `users`, `products`, `vton_results`, `favorites`, `user_usage`, `payments`

Key fields:
- `users`: id, email, name, password_hash, body_measurements (JSON), preferences (JSON), profile_image, is_premium (0/1), plan_type ('free'/'premium'), age, created_at
- `products`: id, external_id, store, name, description, price, currency, original_url, image_url, image_urls (JSON), category, sizes (JSON), colors (JSON), availability, created_at, last_seen
- `vton_results`: id, user_id, product_id, status (pending/processing/completed/failed), input_image_url, output_image_url, garment_image_url, error_message, youcam_task_id, created_at, completed_at
- `payments`: id, user_id, amount, currency, status (pending/completed/failed), transbank_token, plan_type, period_start, period_end, created_at

## Key File Map

| File | Purpose |
|------|---------|
| `workers/src/entry.py` | FastAPI app, CORS, Worker entry, cron handler |
| `workers/src/services/config.py` | Shared constants (limits, thresholds, image constraints) |
| `workers/src/services/auth.py` | JWT (PBKDF2 + HMAC-SHA256), password hashing |
| `workers/src/services/database.py` | D1 CRUD (576 lines) |
| `workers/src/services/llm.py` | LLM recommendations + style chat (Llama 4 Scout) |
| `workers/src/services/vton.py` | YouCam API client |
| `workers/src/services/image_upload.py` | R2/freeimage upload with circuit breaker |
| `workers/src/services/r2.py` | R2 VTON result persistence |
| `workers/src/routes/auth.py` | /register, /login, /refresh |
| `workers/src/routes/products.py` | CRUD products |
| `workers/src/routes/vton.py` | VTON endpoints (generate, prefetch [deprecated], try-on [deprecated], result, webhook, history) |
| `workers/src/routes/payments.py` | Transbank create/confirm/webhook/status |
| `workers/src/routes/scrapers.py` | Manual scraper triggers |
| `workers/src/routes/recommendations.py` | LLM recommendations + chat |
| `workers/src/routes/users.py` | User profile, preferences, premium status |
| `workers/tests/` | 55 tests: auth, config, security, usage_limit, middleware, llm, entry |
| `workers/src/middleware/security.py` | require_auth, optional_auth, require_admin, safe_error_message |
| `workers/src/middleware/usage_limit.py` | Daily VTON/LLM limits (5/day free, unlimited premium) |
| `workers/src/scrapers/` | Active scrapers (Paris, Ripley) |
| `workers/schema.sql` | D1 schema (with gender column + indexes) |
| `workers/migrations/0001_add_gender_and_indexes.sql` | Migration: gender column + indexes |
| `workers/wrangler.jsonc` | Worker config |
| `frontend/src/App.jsx` | React app (BrowserRouter, React.lazy) |
| `frontend/src/store/userSlice.js` | User state (profileStatus: "idle" initial) |
| `frontend/src/store/index.js` | Redux store (no listener middleware) |
| `frontend/src/services/api.js` | Axios client + token refresh |
| `frontend/src/utils/normalize.js` | Gender normalization (hombre/mujer/unisex) |

## Commands

```bash
# Deploy API
cd workers && npx wrangler deploy

# Deploy frontend
cd frontend && npm run build && npx wrangler pages deploy dist --project-name ft-lineone

# Local dev (API)
cd workers && npx wrangler dev

# Local dev (frontend)
cd frontend && npm start

# D1 query
npx wrangler d1 execute ft-lineone-db --command "SELECT COUNT(*) FROM products"

# Run migration
npx wrangler d1 execute ft-lineone-db --file=./migrations/0001_add_gender_and_indexes.sql

# Run tests
cd workers && python -m pytest tests/ -v

# Secrets
npx wrangler secret put JWT_SECRET
npx wrangler secret put TRANSBANK_API_KEY
npx wrangler secret put YOUCAM_API_KEY
```

## 10-Skill Audit Results (2026-07-17)

| # | Skill | Vote | Score | Key Finding |
|---|-------|------|-------|-------------|
| 1 | workers-best-practices | WELL STRUCTURED | 8/10 | Solid CF bindings, PBKDF2, timing-safe JWT. Gaps: hardcoded keys, module-level mutable state |
| 2 | cloudflare-workers-testing | NEEDS IMPROVEMENT | 3/10 | Zero Vitest, test_entry.py tests a copy not real code, no CI gate |
| 3 | fastapi-python | NEEDS IMPROVEMENT | 7/10 | Good async/Pydantic. Gaps: raw dict endpoints, copy-pasted DI, no cache |
| 4 | testing-api-authentication-weaknesses | NEEDS IMPROVEMENT | 5/10 | JWT core solid. Gaps: no logout, no rate limit, webhook unauthenticated, no RBAC |
| 5 | web-scraping | NEEDS IMPROVEMENT | 6/10 | Good resilience. Gaps: no robots.txt, regex HTML parsing, hardcoded keys, duplicate codebase |
| 6 | qa-testing-strategy | NEEDS IMPROVEMENT | 3/10 | Test pyramid missing everything. No CI gate. Scrapers untestable |
| 7 | frontend-react-best-practices | NEEDS IMPROVEMENT | 5/10 | Good code splitting. Gaps: zero React.memo, barrel imports, monolith components |
| 8 | frontend-react-router-best-practices | NEEDS IMPROVEMENT | 4/10 | BrowserRouter only. No ErrorBoundary, no loaders/actions, no zod |
| 9 | tailwindcss-advanced-design-systems | NEEDS IMPROVEMENT | 5/10 | Cohesive aesthetic. Gaps: no semantic tokens, 56 raw color leaks, no dark mode |
| 10 | qa-testing-playwright | NEEDS CREATION | 1/10 | Zero E2E. No playwright.config, no e2e/ directory |

**Consensus**: NEEDS IMPROVEMENT (80%), average score 4.7/10

## Critical Issues (Prioritized)

### FIXED
1. ~~No rate limiting~~ → Added on `/login`, `/register`
2. ~~No logout endpoint~~ → `/logout` with D1 token revocation
3. ~~Webhook Transbank without auth~~ → `require_admin` on payment webhooks
4. ~~No RBAC~~ → `require_admin` on admin/debug/product/scraper routes
5. ~~No logout~~ → Token revocation via `revoked_tokens` table
6. ~~CORS localhost in production~~ → Environment-dependent via `ENVIRONMENT` var
7. ~~Infinite loading bug~~ → `profileStatus: "idle"` initial state
8. ~~Double fetchProfile~~ → Removed redundant listener middleware
9. ~~Usage limits inconsistent~~ → Unified in `services/config.py` (5/5)
10. ~~Scraper data loss~~ → `MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP = 3`
11. ~~YouCam webhook no fail-closed~~ → `YOUCAM_WEBHOOK_FAIL_CLOSED = True`
12. ~~IDOR on /image/{vton_id}~~ → Ownership check + `require_auth` added
13. ~~LLM pre-filtering~~ → Gender/category/colors filter before random sampling
14. ~~Refund logic duplicated~~ → `db.refund_vton_usage()` atomic helper (3 call sites)
15. ~~Error messages leak internals~~ → `safe_error_message()` hides details in production
16. ~~No image validation~~ → Magic bytes + 8MB check on VTON upload
17. ~~Upgrade modal local state~~ → Lifted to `uiSlice.js` (accessible from anywhere)
18. ~~datetime.utcnow() deprecated~~ → `datetime.now(timezone.utc)` across codebase
19. ~~No CI gate~~ → pytest runs on every deploy + standalone `ci.yml` on PRs
20. ~~Schema missing gender~~ → `users.gender` column + indexes added
21. ~~No consolidated VTON endpoint~~ → `POST /vton/generate` replaces prefetch+try-on in one call

### REMAINING
22. Zero E2E tests — no Playwright infrastructure
23. No ErrorBoundary — unhandled error = white screen
24. HTML parsing with regex instead of BeautifulSoup (ripley.py)
25. 56 raw Tailwind color leaks (text-red-500 instead of semantic tokens)
26. No dark mode / fluid typography

## VTON Provider Analysis

**Current**: YouCam API (active, user's decision to keep)

**Alternative (standby)**: FASHN.ai
- Tier I: $19/month (282 credits) + $0.0675/top-up
- On-Demand: $0.075/credit, min $7.50
- 1 credit = 1 try-on
- Migration only when user authorizes

**Self-hosted (future, 5000+ req/month)**: CatVTON on RunPod Serverless
- <8GB VRAM, ~2s inference, $0.69/hr A10G
- Break-even vs FASHN.ai at ~1,000 req/month

**Not feasible**: Running VTON models on Cloudflare Workers AI (no custom model upload, no specialized VTON in catalog)

## LLM + RAG

- **Current**: Llama 4 Scout via Workers AI, prompt-injection approach (no RAG)
- **Product filtering**: Pre-filtered by gender/category/colors before random sampling
- **Cost**: ~$6/month (Workers Paid + AI)
- **Vectorize**: Available for future RAG but not currently used

## Freemium Model

- **Free**: 5 VTON/day + 5 LLM/day
- **Premium**: Unlimited, CLP 4,990/month via Transbank WebPay
- **Test card**: 4051885600446623, CVV 123, RUT 11.111.111-1, Clave 123
- **Limits**: Unified in `services/config.py` — change once, all routes update

## Security Features

- **Rate limiting**: Login (20/IP, 10/email), Register (5/IP/hour)
- **Token revocation**: Logout via D1 `revoked_tokens` table
- **RBAC**: `require_admin` decorator on admin/debug/product/scraper routes
- **CORS**: Environment-dependent — `localhost:3000` allowed only when `ENVIRONMENT != production`
- **Webhook safety**: `YOUCAM_WEBHOOK_FAIL_CLOSED = True` in config
- **Error sanitization**: `safe_error_message()` returns generic message in production
- **Image validation**: Magic bytes + 8MB size check on VTON upload endpoints
- **IDOR protection**: Ownership checks on `/image/{vton_id}` endpoint
- **Atomic usage**: `try_increment_usage()` prevents TOCTOU race conditions
- **Atomic refund**: `refund_vton_usage()` prevents double-refund on concurrent calls

## Config (services/config.py)

All shared constants in one place:
- `VTON_DAILY_LIMIT_FREE = 5`, `LLM_DAILY_LIMIT_FREE = 5` (unified)
- `MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP = 3` (prevents data loss on scraper failure)
- `MAX_USER_IMAGE_BYTES = 8MB`, `ALLOWED_IMAGE_MAGIC` (JPEG/PNG/WebP/HEIC)
- `YOUCAM_WEBHOOK_FAIL_CLOSED = True` (rejects when secret not configured)

## Project Rules

1. **Never commit secrets** — use `wrangler secret put`
2. **Never hardcode API keys** — use env bindings
3. **Always use parameterized queries** — D1 `prepare().bind().run()`
4. **Always `await`** — no floating promises in Workers
5. **Response uses `status=`** not `status_code=`
6. **Gender normalization**: `hombre`/`mujer`/`unisex` via `frontend/src/utils/normalize.js`
7. **Test before deploy** — run `pytest` and `ruff` locally
8. **Branch**: `feat/cloudflare-migration` for all work
