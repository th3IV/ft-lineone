# FT-LineOne Workers API

Cloudflare Workers backend for the FT-LineOne fashion try-on platform.

## Architecture

- **Runtime**: Cloudflare Workers (Python)
- **Database**: Cloudflare D1 (SQLite-based)
- **Storage**: Cloudflare R2 (object storage)
- **AI**: Cloudflare Workers AI (VTON + LLM)

## Setup

### 1. Install Prerequisites

```bash
# Install wrangler (Cloudflare Workers CLI)
npm install -g wrangler

# Install Python workers tool
pip install uv && uv tool install workers-py
```

### 2. Create D1 Database

```bash
npx wrangler d1 create ft-lineone-db
```

Copy the `database_id` and update `wrangler.jsonc`.

### 3. Set Environment Variables

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Set secrets in Cloudflare
pywrangler secret put JWT_SECRET
pywrangler secret put CORS_ORIGINS
```

### 4. Deploy

```bash
cd workers
pywrangler deploy
```

## API Endpoints

### Auth
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token

### Products
- `GET /api/v1/products` - List products with filters
- `GET /api/v1/products/search?q={query}` - Search products
- `GET /api/v1/products/store/{store}` - List by store
- `GET /api/v1/products/{id}` - Get product details

### VTON
- `POST /api/v1/vton/try-on` - Process virtual try-on
- `GET /api/v1/vton/result/{id}` - Get result
- `GET /api/v1/vton/history` - Get history

### Recommendations
- `GET /api/v1/recommendations` - Get recommendations
- `POST /api/v1/recommendations/chat` - Style advice

### Scrapers
- `POST /api/v1/scrapers/ingest` - Ingest product
- `POST /api/v1/scrapers/ingest/batch` - Batch ingest

## Development

```bash
cd workers
pip install -e ".[dev]"
pywrangler dev
```

## Limitations (Free Tier)

- Workers: 100,000 requests/day
- D1: 5GB storage, 10M reads/day
- R2: 10GB storage
- Workers AI: 10,000 neurons/day
