# Expensr

Aplicación de gestión de gastos empresariales con frontend React + Vite, backend FastAPI y PostgreSQL. El flujo de validación se integra con IBM BAW. La integración con Appian está pendiente de completar.

## Requisitos

- Docker y Docker Compose.
- `uv` para el desarrollo del backend.
- Node.js y `pnpm` para el desarrollo del frontend.
- `kubectl` y un clúster Kubernetes local para el despliegue en Kubernetes.
- ngrok para que BAW pueda acceder a los endpoints de Expensr en el entorno local.

## Configuración local

Docker Compose lee las credenciales de PostgreSQL desde un archivo `.env` en la raíz del proyecto. Si no existe, créalo con estos nombres de variables y valores locales:

```dotenv
POSTGRES_DB=expensr
POSTGRES_USER=expensr
POSTGRES_PASSWORD=cambia-esta-contraseña-local
```

El backend lee sus variables desde `expensr-backend/.env`. Crea ese archivo a partir de la plantilla:

```bash
cp expensr-backend/.env.example expensr-backend/.env
```

Configura en el archivo del backend las variables necesarias para Gemini, BAW y Appian. No compartas ni subas archivos `.env`, claves API o contraseñas al repositorio.

## Arranque con Docker Compose

Desde la raíz del proyecto:

```bash
docker compose up -d --build
docker compose ps
```

Direcciones locales:

- Aplicación web: http://localhost:8081
- API a través de nginx: http://localhost:8081/api/
- Swagger: http://localhost:8081/api/docs

Ver logs:

```bash
docker compose logs -f
```

Detener los servicios conservando los datos de PostgreSQL:

```bash
docker compose down
```

La base de datos utiliza un volumen Docker. `docker compose down` conserva ese volumen y sus datos.

## Desarrollo local

### Backend

```bash
cd expensr-backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

La API y Swagger quedan disponibles en:

- http://localhost:8000
- http://localhost:8000/docs

### Frontend

En otra terminal:

```bash
cd expensr-frontend
pnpm install
pnpm run dev
```

## ngrok para BAW con Docker Compose

Con Docker Compose iniciado, expón el puerto de nginx. El mismo túnel permite acceder al frontend y a las rutas que nginx reenvía al backend:

```bash
ngrok http 8081 --domain=tameness-hamburger-proton.ngrok-free.dev
```

Mantén ngrok abierto mientras BAW necesite comunicarse con Expensr. La interfaz utiliza rutas bajo `/api/`; las llamadas REST configuradas en BAW utilizan rutas como `/expenses/{gasto_id}` y `/baw/expenses/{gasto_id}/validation`.

## Despliegue local en Kubernetes

El despliegue comprobado se ejecutó en el contexto Kubernetes de Docker Desktop. El enunciado del proyecto menciona Minikube o Kind; confirma con el tutor si Docker Desktop se acepta como alternativa para la entrega final.

Desde la raíz del proyecto, crea el namespace y el ConfigMap de inicialización:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -n expensr -f k8s/db-init-configmap.yaml
```

Crea los Secrets en el clúster. Los valores se leen localmente desde los archivos `.env` y no se guardan en el repositorio:

```bash
set -a
source .env
set +a

kubectl create secret generic expensr-db-credentials \
  --namespace expensr \
  --from-literal=POSTGRES_DB="$POSTGRES_DB" \
  --from-literal=POSTGRES_USER="$POSTGRES_USER" \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD"

kubectl create secret generic expensr-db-connection \
  --namespace expensr \
  --from-literal="DATABASE_URL=postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"

kubectl create secret generic expensr-backend-env \
  --namespace expensr \
  --from-env-file=expensr-backend/.env

unset POSTGRES_PASSWORD
```

Construye las imágenes y despliega los servicios en este orden:

```bash
docker compose build backend frontend
kubectl apply -n expensr -f k8s/postgres.yaml
kubectl rollout status statefulset/expensr-postgres -n expensr
kubectl apply -n expensr -f k8s/backend.yaml
kubectl rollout status deployment/expensr-backend -n expensr
kubectl apply -n expensr -f k8s/frontend.yaml
kubectl rollout status deployment/expensr-frontend -n expensr
```

Comprueba pods, servicios y almacenamiento:

```bash
kubectl get pods,services,pvc -n expensr
```

Para acceder a la aplicación, mantén el siguiente comando activo en una terminal:

```bash
kubectl port-forward -n expensr service/expensr-frontend 8082:80
```

Abre http://localhost:8082. Para comprobar que nginx llega al backend:

```bash
curl -i http://localhost:8082/api/expenses/
```

Kubernetes utiliza su propio PostgreSQL y su propio volumen, separados de los de Docker Compose. Por eso, en una instalación nueva aparecen los datos semilla y no las facturas guardadas en el entorno Compose.

## Comprobaciones del backend

Desde `expensr-backend`, ejecuta:

```bash
just check
```

Este comando ejecuta las comprobaciones de Ruff y las pruebas del backend.
