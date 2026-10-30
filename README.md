# Expensr

Expensr permite registrar gastos y seguir su validación y decisión financiera. Incluye una aplicación web, una API, PostgreSQL e integraciones con IBM BAW y Appian. También permite extraer datos de facturas y consultar gastos mediante un chatbot.

## Funcionalidades

- Registro y consulta de gastos.
- Extracción de fecha, importe, categoría y concepto de facturas mediante Gemini.
- Inicio y seguimiento del proceso de validación en IBM BAW.
- Consulta de datos financieros y registro de decisiones de Appian.
- Chatbot para consultar gastos, estados y tiempos medios.
- Monitorización de gastos, KPI y disponibilidad de BAW y Appian.

La extracción de facturas admite PDF, JPG, PNG y WEBP, con un tamaño máximo de 10 MB. Los datos extraídos se muestran para que el usuario los revise antes de registrar el gasto.

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Frontend | React 19, Vite, React Router, Tailwind CSS y Recharts |
| Backend | Python 3.12 o superior, FastAPI, SQLAlchemy 2 y Pydantic 2 |
| Base de datos | PostgreSQL 17 |
| OCR y chatbot | Google Gemini mediante `google-genai` |
| Validación | IBM Business Automation Workflow (BAW) |
| Decisión financiera | Appian |
| Despliegue | Docker Compose, Kubernetes y Nginx |

## Estructura

```text
ProyectoExpensr/
├── certs/                  Certificados utilizados para la conexión con BAW
├── docs/                   Documentación de arquitectura, decisiones y datos
├── exports/
│   ├── appian/             Exportación de Appian
│   └── baw/                Exportación del proceso BAW
├── expensr-backend/
│   ├── app/                 API, modelos, routers y servicios
│   ├── sql/                 Esquema y datos iniciales
│   └── tests/               Pruebas del backend
├── expensr-frontend/       Aplicación React y configuración de Nginx
├── k8s/                    Manifiestos de Kubernetes
└── docker-compose.yml      Configuración de Docker Compose
```

## Variables de entorno

Crea los archivos locales a partir de los ejemplos:

```bash
cp .env.example .env
cp expensr-backend/.env.example expensr-backend/.env
```

El `.env` de la raíz se usa en Docker Compose. Incluye las variables de PostgreSQL y `NGROK_AUTHTOKEN`.

`expensr-backend/.env` contiene la configuración del backend:

- `GEMINI_API_KEY`
- `BAW_BASE_URL`, `BAW_USER`, `BAW_PASSWORD`, `BAW_BPD_ID` y `BAW_PROCESS_APP_ID`
- `BAW_CA_BUNDLE`
- `APPIAN_BASE_URL` y `APPIAN_API_KEY`
- `DEMO_EMPLOYEE`

Configura las credenciales de BAW, Appian y Gemini en el entorno local. No añadas valores reales a los archivos de ejemplo ni los subas a Git.

## Docker Compose

Desde la raíz del proyecto, inicia los servicios con:

```bash
docker compose up -d --build
```

Comprueba su estado:

```bash
docker compose ps
```

| Servicio | Dirección |
| --- | --- |
| Aplicación web | `http://localhost:8081` |
| Monitor | `http://localhost:8081/monitor` |
| PostgreSQL | `localhost:5432` |

El backend no publica su puerto directamente en el host; el frontend se comunica con él dentro de la red de Compose. El servicio ngrok de Compose dirige el tráfico a ese frontend.

Los datos de PostgreSQL se guardan en el volumen `postgres_data`.

## Desarrollo local

El backend necesita una instancia de PostgreSQL disponible y su archivo de entorno configurado:

```bash
cd expensr-backend
uv run uvicorn app.main:app --reload --port 8000
```

En otra terminal, inicia el frontend:

```bash
cd expensr-frontend
pnpm install
pnpm dev
```

Vite sirve el frontend en `http://localhost:5173`. Por defecto, el cliente busca la API en `http://127.0.0.1:8000`; se puede cambiar con `VITE_API_URL`.

## Kubernetes

Los manifiestos están en `k8s/` y usan el namespace `expensr`. Antes de desplegar los servicios, crea los Secrets y ConfigMaps que requieren los manifiestos.

### Preparar la configuración

Crea el namespace y el ConfigMap de inicialización de PostgreSQL:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -n expensr -f k8s/db-init-configmap.yaml
```

Crea estos Secrets con los valores de tu entorno:

- `expensr-db-credentials`: claves `POSTGRES_DB`, `POSTGRES_USER` y `POSTGRES_PASSWORD`.
- `expensr-db-connection`: clave `DATABASE_URL`, con una URL que use el servicio interno `postgres`.
- `expensr-backend-env`: configuración del backend. Se puede generar desde el archivo local:

  ```bash
  kubectl create secret generic expensr-backend-env \
    -n expensr \
    --from-env-file=expensr-backend/.env \
    --dry-run=client -o yaml | kubectl apply -f -
  ```

- `ngrok-auth`: clave `authtoken` con el token de ngrok.

Crea también el ConfigMap del certificado de BAW:

```bash
kubectl create configmap baw-ca \
  -n expensr \
  --from-file=baw-ca.pem=certs/baw-ca.pem \
  --dry-run=client -o yaml | kubectl apply -f -
```

No guardes contraseñas ni tokens en los manifiestos.

### Desplegar los servicios

Despliega PostgreSQL y espera a que esté listo:

```bash
kubectl apply -n expensr -f k8s/postgres.yaml
kubectl wait -n expensr \
  --for=condition=Ready pod \
  -l app=expensr-postgres \
  --timeout=180s
```

Despliega el backend, el frontend y ngrok:

```bash
kubectl apply -n expensr -f k8s/backend.yaml
kubectl apply -n expensr -f k8s/frontend.yaml
kubectl apply -f k8s/ngrok.yaml
```

Comprueba los pods y despliegues:

```bash
kubectl get pods -n expensr
kubectl rollout status deployment/expensr-backend -n expensr
kubectl rollout status deployment/expensr-frontend -n expensr
kubectl rollout status deployment/expensr-ngrok -n expensr
```

El frontend y el backend usan servicios `ClusterIP`. Para abrir el frontend desde el equipo local:

```bash
kubectl port-forward -n expensr service/expensr-frontend 8080:80
```

Abre `http://localhost:8080`.

Para abrir Swagger UI del backend, en otra terminal ejecuta:

```bash
kubectl port-forward -n expensr service/expensr-backend 8001:8000
```

Abre `http://localhost:8001/docs`.

El manifiesto `k8s/ngrok.yaml` publica el frontend de Kubernetes. Si se usa el mismo dominio ngrok para Docker y Kubernetes, asegúrate de que el tráfico llegue al entorno que quieres probar.

## API

El backend incluye, entre otros, estos endpoints:

| Método y ruta | Uso |
| --- | --- |
| `GET /expenses/` | Lista los gastos |
| `GET /expenses/{gasto_id}` | Consulta un gasto |
| `POST /expenses/` | Registra un gasto e intenta iniciar el proceso BAW |
| `POST /extract-invoice` | Extrae datos de una factura |
| `POST /chat/` | Envía una consulta al chatbot |
| `GET /monitor/overview` | Devuelve KPI, instancias y estado de las fuentes |
| `POST` o `PATCH /baw/expenses/{gasto_id}/validation` | Guarda los datos de validación BAW |
| `POST` o `PATCH /baw/expenses/{gasto_id}/decision` | Guarda la resolución BAW |
| `GET /appian/expenses/{gasto_id}/decision-context` | Consulta los datos para la decisión financiera |
| `POST /appian/expenses/{gasto_id}/decision` | Guarda la decisión de Appian |

## Bases de datos e integraciones

Docker Compose y Kubernetes mantienen bases PostgreSQL independientes:

- Docker Compose usa el volumen `postgres_data`.
- Kubernetes usa un volumen persistente asociado al StatefulSet `expensr-postgres`.

Los datos no se sincronizan automáticamente entre ambas bases.

El backend es quien lee y escribe los datos de Expensr. BAW y Appian intercambian información con el backend mediante API; no acceden directamente a PostgreSQL por JDBC ni mediante un Data Store de Appian.

## Comprobaciones

Backend:

```bash
cd expensr-backend
uv run ruff format --check .
uv run ruff check .
uv run pytest -v
```

Frontend:

```bash
cd expensr-frontend
pnpm install
pnpm lint
pnpm build
```
