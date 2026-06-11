# FT. THE LINE ONE

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4-06B6D4?logo=tailwindcss&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2-EE4C2C?logo=pytorch&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-EKS-FF9900?logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-1.10-844FBA?logo=terraform&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-GPT4-1C3C3C?logo=langchain&logoColor=white)
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
- **infra/** — Infraestructura como código con Terraform + AWS
- **docs/** — Documentación técnica

## Estructura del Proyecto

```
ft-lineone/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── products.py
│   │   │   │   ├── recommendations.py
│   │   │   │   └── vton.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── domain/
│   │   │   ├── models/
│   │   │   │   ├── user.py
│   │   │   │   └── product.py
│   │   │   └── schemas/
│   │   │       ├── auth.py
│   │   │       ├── user.py
│   │   │       ├── product.py
│   │   │       └── vton.py
│   │   ├── application/
│   │   │   ├── services/
│   │   │   │   ├── user_service.py
│   │   │   │   ├── product_service.py
│   │   │   │   ├── recommendation_service.py
│   │   │   │   └── vton_service.py
│   │   │   └── interfaces/
│   │   │       ├── scraper_client.py
│   │   │       └── llm_client.py
│   │   ├── infrastructure/
│   │   │   ├── repositories/
│   │   │   │   ├── user_repository.py
│   │   │   │   └── product_repository.py
│   │   │   ├── clients/
│   │   │   │   ├── s3_client.py
│   │   │   │   ├── scraper_client.py
│   │   │   │   └── llm_client.py
│   │   │   └── database/
│   │   │       ├── session.py
│   │   │       └── models.py
│   │   └── main.py
│   ├── alembic/
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
│   ├── base_scraper.py
│   ├── falabella.py
│   ├── ripley.py
│   ├── paris.py
│   ├── maui.py
│   ├── zara.py
│   ├── orchestrator.py
│   ├── requirements.txt
│   └── Dockerfile
├── vton/
│   ├── models/
│   ├── services/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── infra/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── vpc/
│   │   │   ├── eks/
│   │   │   ├── rds/
│   │   │   └── s3/
│   │   └── environments/
│   │       ├── dev/
│   │       └── prod/
│   ├── kubernetes/
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   └── ingress.yaml
│   └── scripts/
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
| **Infraestructura** | AWS (EKS, RDS, S3) + Terraform | 1.10 |
| **IA** | LangChain + GPT-4 | — |
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
|---|---|---|---|
| POST | /api/v1/auth/register | Registro de usuario | No |
| POST | /api/v1/auth/login | Inicio de sesión | No |
| POST | /api/v1/auth/refresh | Renovar token | No |
| GET | /api/v1/users/me | Perfil del usuario | Sí |
| PUT | /api/v1/users/me/measurements | Actualizar medidas | Sí |
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
