---
name: docs
description: >
  Use when asked to update README.md, docs/api.md, or docs/architecture.md.
  Ensures documentation stays synchronized with the actual code structure,
  endpoints, and architecture.
---

# Documentación Skill

Mantener la documentación del proyecto sincronizada con el código real.

## Archivos de documentación
| Archivo | Contenido |
|---|---|
| `README.md` | Visión general, setup, estructura, endpoints |
| `docs/api.md` | Documentación detallada de endpoints REST |
| `docs/architecture.md` | Arquitectura, diagramas, jerarquía de clases |

## Convenciones

### Cuándo actualizar docs
- **README.md**: al cambiar estructura de directorios, agregar/quitar endpoints, cambiar stack tecnológico
- **docs/api.md**: al agregar, modificar o eliminar endpoints. Responses y requests deben reflejar el schema real
- **docs/architecture.md**: al cambiar la arquitectura, agregar/quitar servicios, cambiar paths de directorios

### Reglas
- `docs/api.md` debe coincidir exactamente con los responses del código
- `docs/architecture.md` debe reflejar la estructura real de directorios y clases
- `README.md` debe tener el árbol de directorios actualizado
- No crear archivos de documentación adicionales a menos que se solicite explícitamente
