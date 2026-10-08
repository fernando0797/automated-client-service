# Backend

API FastAPI para el sistema de atención automatizada. Esta carpeta es
autocontenida: incluye código, base de conocimiento, migraciones, dependencias
y un Docker Compose con PostgreSQL.

## Contenido

```text
alembic/              Migraciones de base de datos
knowledge/            Base documental utilizada por el RAG
scripts/              Comprobaciones manuales de persistencia
src/                  Código de la aplicación
tests/                Pruebas automatizadas
.env.example          Variables requeridas sin secretos
Dockerfile            Imagen de la API
docker-compose.yml    API y PostgreSQL para un despliegue independiente
requirements.txt      Dependencias de ejecución
requirements-dev.txt  Dependencias adicionales para pruebas
```

## Desarrollo local sin Docker

Desde esta carpeta:

```bash
python -m venv .venv
```

En Windows:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
uvicorn src.api.main:app --reload
```

En Linux o macOS:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
uvicorn src.api.main:app --reload
```

La aplicación requiere PostgreSQL y un archivo `.env` basado en
`.env.example`.

## Despliegue independiente en EC2

1. Copia esta carpeta `backend/` a la instancia.
2. Crea el archivo de configuración:

```bash
cp .env.example .env
chmod 600 .env
```

3. Edita `.env` y establece claves y contraseñas reales. En
   `CORS_ORIGINS` indica la URL HTTPS exacta del frontend, sin una barra final.
4. Construye y arranca la API y PostgreSQL:

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

5. Comprueba el despliegue:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

El Compose no publica el puerto de PostgreSQL. Solo publica el puerto 8000 de
la API. En producción conviene colocar un proxy HTTPS delante de ese puerto y
limitar el grupo de seguridad de EC2 a los accesos necesarios.

## Variables principales

- `GOOGLE_API_KEY`: clave del proveedor LLM.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: credenciales de la base.
- `POSTGRES_HOST`, `POSTGRES_PORT`: conexión a PostgreSQL.
- `CORS_ORIGINS`: lista separada por comas de orígenes frontend permitidos.

Nunca añadas `.env` al repositorio. Si una credencial se publica, revócala y
genera una nueva; eliminar únicamente el archivo de Git no invalida la clave.
