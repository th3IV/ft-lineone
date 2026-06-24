# Setup y Desarrollo Local

## Prerrequisitos

- Python 3.12+
- Node.js 18+
- Docker (opcional)
- PostgreSQL 16 (o SQLite para desarrollo)

## Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm start
# Abre en http://localhost:3000
```

## Scrapers

```bash
cd scrapers
python -m venv venv
pip install -r requirements.txt
python orchestrator.py
```

## VTON

```bash
cd vton
python -m venv venv
pip install -r requirements.txt
python app.py
```

## Variables de Entorno

Copiar `.env.example` → `.env` y configurar:

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Conexión PostgreSQL (o SQLite por defecto) |
| `JWT_SECRET` | Clave secreta para JWT |
| `GOOGLE_API_KEY` | API key para Gemini LLM |
| `SCRAPER_API_URL` | URL del servicio scrapers |
| `VTON_API_URL` | URL del servicio VTON |

## Notas

- Por defecto usa SQLite (`sqlite+aiosqlite:///./ft_lineone.db`)
- El LLM usa Gemini 2.0 Flash como fallback si no hay API key configurada

## Enlaces

- [[docs/api]]
- [[Arquitectura]]
- [[Backend — Detalle Técnico]]
