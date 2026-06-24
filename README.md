# FT. THE LINE ONE

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4-06B6D4?logo=tailwindcss&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2-EE4C2C?logo=pytorch&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Descripción

**FT. THE LINE ONE** es una plataforma **B2C de Fashion Tech** que integra **Web Scraping**, **Inteligencia Artificial (LLMs)** y **Virtual Try-On (VTON)** para ofrecer una experiencia de compra de moda inteligente y personalizada.

La plataforma extrae productos en tiempo real desde los principales retailers de Chile (Falabella, Ripley, Paris, Maui, Zara), los procesa con IA, y permite a los usuarios probarse virtualmente la ropa antes de comprar.

## Arquitectura

Monorepo estructurado en 4 microservicios:

- **backend/** — API REST con FastAPI, PostgreSQL, autenticación JWT
- **frontend/** — Aplicación React con TailwindCSS
- **scrapers/** — Módulos de scraping con BeautifulSoup
- **vton/** — Servicio de Virtual Try-On con modelos de difusión (PyTorch)
- **docs/** — Documentación técnica

## Estructura del Proyecto

```
ft-lineone/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routes/
│   │   │           ├── auth.py
│   │   │           ├── users.py
│   │   │           ├── products.py
│   │   │           ├── recommendations.py
│   │   │           └── vton.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── domain/
│   │   │   └── models/
│   │   │       ├── user.py
│   │   │       ├── product.py
│   │   │       └── vton_result.py
│   │   ├── application/
│   │   │   ├── services/
│   │   │   │   ├── user_service.py
│   │   │   │   ├── product_service.py
│   │   │   │   ├── recommendation_service.py
│   │   │   │   └── vton_service.py
│   │   │   └── orchestrator/
│   │   │       ├── pipeline_orchestrator.py
│   │   │       ├── scraping_coordinator.py
│   │   │       ├── vton_coordinator.py
│   │   │       └── publication_manager.py
│   │   ├── infrastructure/
│   │   │   ├── persistence/
│   │   │   │   └── postgres/
│   │   │   │       ├── models.py
│   │   │   │       └── repositories/
│   │   │   │           ├── user_repository.py
│   │   │   │           └── product_repository.py
│   │   │   └── external_services/
│   │   │       ├── llm_client.py
│   │   │       ├── vton_client.py
│   │   │       └── scraper_client.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── index.jsx
│   ├── package.json
│   └── Dockerfile
├── scrapers/
│   ├── scrapers/
│   │   ├── base_scraper.py
│   │   ├── falabella.py
│   │   ├── ripley.py
│   │   ├── paris.py
│   │   ├── maui.py
│   │   └── zara.py
│   ├── models/
│   │   └── product_dto.py
│   ├── pipeline/
│   │   └── orchestrator.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── vton/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── docs/
│   ├── architecture.md
│   └── api.md
├── .env.example
├── .gitignore
└── README.md
```

## Tech Stack

| Capa | Tecnología | Versión |
|---|---|---|
| **Backend** | FastAPI + Python | 3.12+ / 0.115 |
| **Frontend** | React + JavaScript + TailwindCSS | 19 / 4 |
| **Scrapers** | Python + BeautifulSoup | 4.x |
| **VTON** | Diffusion Models + PyTorch | 2.x |

| **IA** | Gemini 2.0 Flash | — |
| **Base de Datos** | PostgreSQL + Redis | 16 / 7 |
| **Autenticación** | JWT + bcrypt | — |

## Getting Started

### Prerrequisitos

- Python 3.12+
- Node.js 18+
- Docker (opcional, para contenedores)
- PostgreSQL 16 (o Docker para BD local)

### Clonar el repositorio

```bash
git clone https://github.com/tu-org/ft-lineone.git
cd ft-lineone
```

### Backend

```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

La aplicación se abrirá en `http://localhost:3000`.

### Scrapers

```bash
cd scrapers
python -m venv venv
pip install -r requirements.txt
python orchestrator.py
```

### VTON

```bash
cd vton
python -m venv venv
pip install -r requirements.txt
python app.py
```

## API Endpoints

| Método | Ruta | Descripción | Auth |
|---|---|---|---|---|
| POST | /api/v1/auth/register | Registro de usuario | No |
| POST | /api/v1/auth/login | Inicio de sesión | No |
| POST | /api/v1/auth/refresh | Renovar token | No |
| GET | /api/v1/users/me | Perfil del usuario | Sí |
| PUT | /api/v1/users/me/measurements | Actualizar medidas corporales | Sí |
| GET | /api/v1/users/me/history | Historial de interacciones | Sí |
| GET | /api/v1/products | Listar productos | No |
| GET | /api/v1/products/{id} | Detalle del producto | No |
| GET | /api/v1/products/search | Buscar productos | No |
| GET | /api/v1/products/store/{store} | Productos por tienda | No |
| GET | /api/v1/recommendations | Recomendaciones IA | Sí |
| POST | /api/v1/vton/try-on | Virtual Try-On | Sí |
| GET | /api/v1/vton/result/{id} | Resultado VTON | Sí |

## Variables de Entorno

Copiar `.env.example` a `.env` y configurar:

```bash
cp .env.example .env
```

Las variables requeridas están documentadas en [.env.example](.env.example).

## Licencia

Distribuido bajo licencia MIT. Ver [LICENSE](LICENSE) para más información.
