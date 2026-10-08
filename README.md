# TFG - Automated Client Service

Monorepo con el backend de soporte automatizado y su interfaz web.

## Estructura

```text
backend/          API FastAPI, agentes, RAG, PostgreSQL y migraciones
frontend/         Aplicación web TanStack/Vite
datas/            Datos locales; no se versionan
docker-compose.yml Entorno completo para desarrollo local
```

Cada aplicación tiene su propio Dockerfile, dependencias y configuración. La
carpeta `backend/` también incluye un `docker-compose.yml` independiente para
poder copiarla o desplegarla por separado en una instancia EC2.

## Arranque local del proyecto completo

1. Copia `backend/.env.example` como `backend/.env`.
2. Sustituye los valores de ejemplo, especialmente `GOOGLE_API_KEY` y
   `POSTGRES_PASSWORD`.
3. Si el frontend no debe usar `http://localhost:8000`, copia `.env.example`
   como `.env` y cambia `VITE_API_URL`.
4. Ejecuta:

```bash
docker compose up --build
```

Servicios locales:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Documentación de la API: http://localhost:8000/docs
- Adminer: http://localhost:8080

## Configuración sensible

Los archivos `.env` y `.env.local` están excluidos de Git. Los archivos
`.env.example` documentan las variables necesarias y nunca deben contener
credenciales reales.

Consulta `backend/README.md` para ejecutar pruebas o desplegar únicamente el
backend en EC2.
