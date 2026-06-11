---
name: vton
description: >
  Use when working on the Virtual Try-On service: inference pipelines,
  model integration, or API endpoints for try-on with PyTorch diffusion models.
---

# VTON (Virtual Try-On) Skill

Servicio de Virtual Try-On con modelos de difusión (PyTorch) para probar ropa virtualmente.

## Estructura
```
vton/
├── app/
│   ├── api/        # FastAPI endpoints
│   ├── services/   # Lógica de VTON
│   ├── models/     # Modelos PyTorch
│   └── main.py
├── tests/
├── requirements.txt
└── Dockerfile
```

## Setup
```powershell
cd vton
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python app/main.py
```

## Flujo
1. Backend envía imagen de usuario + prenda vía HTTP POST
2. VTON procesa con modelo de difusión
3. Guarda resultado en S3
4. Backend consulta resultado vía GET

## Convenciones
- Endpoints expuestos en `app/api/` con FastAPI
- Lógica de inferencia en `app/services/`
- Modelos PyTorch en `app/models/`
- Comunicación con backend vía HTTP/JSON
- Timeout mínimo 300s para requests de inferencia
