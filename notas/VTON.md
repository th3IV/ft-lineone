# Virtual Try-On (VTON)

> Servicio de IA generativa en `:8002`. Modelo de difusión para probarse ropa virtualmente.

## Arquitectura

```
Frontend → Backend (solicitud VTON) → VTON Service (procesa imagen)
                                              ↕
                                        LocalStorage (resultado)
```

## Estados del Proceso

| Estado | Descripción |
|--------|-------------|
| `pending` | Solicitud recibida, en cola |
| `processing` | Modelo generando la imagen |
| `completed` | Resultado disponible |
| `failed` | Error en el proceso |

## Endpoints del VTON Service

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/try-on` | Iniciar try-on (JSON o multipart) |
| GET | `/try-on/{job_id}/status` | Consultar estado |
| GET | `/try-on/{job_id}/result` | Obtener resultado |

## Tech Stack

- **Framework**: PyTorch
- **API**: FastAPI
- **Storage**: LocalStorage

## Archivos Clave

- `vton/app/api/routes.py` — Endpoints del servicio VTON
- `vton/app/services/try_on_service.py` — Lógica del modelo
- `backend/app/domain/models/vton_result.py` — Modelo VTONResult
- `backend/app/infrastructure/external_services/vton_client.py` — Cliente HTTP
- `backend/app/api/v1/routes/vton.py` — Endpoints del backend para VTON

## Configuración

En `backend/app/core/config.py`:
```python
VTON_API_URL: str = "http://localhost:8002"
```

## Enlaces

- [[Arquitectura]]
- [[API Endpoints]]
