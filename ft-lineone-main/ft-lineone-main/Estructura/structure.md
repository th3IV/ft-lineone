# FT. THE LINE ONE - Stack de Capa Gratuita y Estructura del Proyecto

Este documento detalla la arquitectura alternativa de costo cero ($0 USD) para el desarrollo y despliegue del MVP del proyecto, manteniendo los principios de Clean Architecture y Programación Orientada a Objetos (POO) planteados originalmente.

---

## 1. Stack Tecnológico (Free Tier)

Para optimizar costos durante las fases de desarrollo y QA, se sustituye la infraestructura de AWS por servicios Serverless y PaaS con capas gratuitas altamente generosas:

| Componente Original (AWS) | Alternativa Gratuita Seleccionada | Propósito en el Proyecto |
| :--- | :--- | :--- |
| **Amazon EKS (Kubernetes)** | **Render / Railway** | Hospedaje del backend en FastAPI (Python). |
| **Amazon RDS (PostgreSQL)** | **Supabase** | Persistencia de usuarios, medidas y el Style Quiz. |
| **Amazon DocumentDB** | **MongoDB Atlas (M0)** | Catálogos no estructurados de Web Scraping. |
| **Amazon S3** | **Cloudinary** | Almacenamiento y optimización de imágenes CDN. |
| **Amazon ElastiCache (Redis)** | **Upstash Redis** | Caché de sesiones y respuestas del AI Advisor. |
| **OpenAI GPT-4 API** | **Google AI Studio (Gemini 1.5 Flash)** | Motor de inferencia del Agente de IA sin costo por token. |
| **Instancia GPU (VTON)** | **Hugging Face Spaces (CPU/Gpu Low)** | Wrapper e inferencia del modelo de difusión de ropa. |

---

## 2. Estructura del Proyecto (Clean Architecture)

El código fuente del backend (`src/`) se organiza en capas independientes de la infraestructura. Esto garantiza que migrar de regreso a AWS en el futuro solo requiera cambiar los adaptadores de la capa `infrastructure`, sin tocar la lógica de negocio.

```text
ft-the-line-one-backend/
│
├── .github/workflows/       # CI/CD para despliegue automático en Render
├── docs/                    # Documentación técnica e instructivos
├── requirements.txt         # Dependencias del proyecto (FastAPI, LangChain, Motor, SQLAlchemy)
├── README.md
│
└── src/                     # Código fuente principal
    │
    ├── domain/              # CAPA DE DOMINIO: Modelos de negocio puros y contratos (Interfaces)
    │   ├── entities/        # Entidades POO puras (Sin frameworks)
    │   │   ├── __init__.py
    │   │   ├── user.py      # Clase User (Medidas, perfil)
    │   │   ├── product.py   # Clase Product (Prendas del scraping)
    │   │   └── session.py   # Clase Session (Sesión de chat/usuario)
    │   │
    │   └── interfaces/      # Contratos de repositorios y servicios externos
    │       ├── user_repository.py
    │       ├── product_repository.py
    │       └── ai_advisor_interface.py
    │
    ├── application/         # CAPA DE APLICACIÓN: Casos de uso y lógica de los agentes de IA
    │   ├── use_cases/       # Flujos de interacción del sistema
    │   │   ├── process_quiz.py
    │   │   └── trigger_vton.py
    │   │
    │   └── agents/          # Orquestación de IA y Skills (Responsabilidad Persona 2)
    │       ├── fashion_advisor_agent.py
    │       └── skills/
    │           ├── recommend_products/
    │           │   ├── skill.md       # Manifiesto técnico para el LLM
    │           │   ├── schema.py      # Validación Pydantic de entrada
    │           │   └── service.py     # Lógica que conecta la skill al repositorio
    │           └── virtual_try_on/
    │               ├── skill.md
    │               └── service.py     # Comunicación con Hugging Face Spaces
    │
    ├── infrastructure/      # CAPA DE INFRAESTRUCTURA: Implementaciones de herramientas y BD
    │   ├── database/        # Conexiones y ORM
    │   │   ├── postgres/    # Adaptadores para Supabase (SQLAlchemy)
    │   │   └── mongodb/     # Adaptadores para MongoDB Atlas (Motor)
    │   │
    │   ├── repositories/    # Implementación real de las interfaces del dominio
    │   │   ├── pg_user_repository.py
    │   │   └── mongo_product_repository.py
    │   │
    │   ├── scrapers/        # Motores de Scraping (Responsabilidad Persona 2)
    │   │   ├── base_scraper.py
    │   │   ├── zara_scraper.py
    │   │   └── hm_scraper.py
    │   │
    │   └── external_services/ # Clientes de APIs externas
    │       ├── google_ai_client.py  # Conexión con Google AI Studio
    │       ├── cloudinary_client.py # Gestión de imágenes
    │       └── redis_client.py      # Conexión con Upstash Redis
    │
    └── main.py              # Punto de entrada de la aplicación (Configuración de FastAPI)