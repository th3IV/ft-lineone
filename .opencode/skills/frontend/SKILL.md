---
name: frontend
description: >
  Use when working on the React frontend: components, pages, hooks, services,
  or styling with TailwindCSS. Covers setup and code conventions.
---

# Frontend Skill

Aplicación React + JavaScript + TailwindCSS. Interfaz de usuario B2C para la plataforma de moda.

## Setup
```powershell
cd frontend
npm install
npm start
```

## Convenciones

### Nuevo componente
1. Crear en `src/components/` con nombre PascalCase (Ej: `Button.jsx`, `ProductCard.jsx`)
2. Usar funciones flecha con export default
3. Estilos con TailwindCSS utility classes

### Nueva página
1. Crear en `src/pages/`
2. Una página por ruta

### Nuevo hook
1. Crear en `src/hooks/` con prefijo `use` (Ej: `useAuth.js`, `useProducts.js`)
2. Llamadas API asíncronas con try/catch

### Nuevo servicio API
1. Crear en `src/services/`
2. Llamar a `http://localhost:8000/api/v1/...`

### Estilos
- TailwindCSS v4 utility classes
- No usar CSS modules ni styled-components
