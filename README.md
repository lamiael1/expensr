# Expensr

Aplicación web para registrar y consultar gastos empresariales. Integra React + Vite, FastAPI, PostgreSQL, IBM BAW, Appian, IA generativa y despliegue local con Docker y Kubernetes.

## Funcionalidades

- Subida de facturas: el backend envía imágenes o PDF a Gemini para extraer fecha, importe, categoría y concepto. El empleado revisa los datos antes de registrar el gasto.
- Mis gastos: consulta del histórico de gastos.
- Chatbot: respuestas en español con function calling para listar gastos, consultar estados y calcular tiempos medios. Las funciones reciben la identidad de demostración desde el backend.
- Monitoreo: KPIs, gráfico por etapa y tabla de instancias. FastAPI consulta BAW y el Web API de Appian, unifica resultados y presenta avisos si una fuente falla.
- Aprobación: FastAPI registra el gasto e intenta iniciar BAW. Appian toma la decisión financiera y la devuelve a Expensr mediante una API.

## Arquitectura

    Navegador → React/Vite servido por Nginx → /api → FastAPI → PostgreSQL
                                                        ├→ IBM BAW (REST)
                                                        ├→ Appian (Web APIs)
                                                        └→ Gemini (OCR y chatbot)

ngrok publica Nginx, que enruta las solicitudes /api hacia FastAPI. Las credenciales permanecen en el entorno del backend/despliegue, nunca en el bundle del frontend.

## Requisitos

- Docker Desktop y Docker Compose.
- Para Kubernetes: Docker Desktop con Kubernetes habilitado y kubectl.
- Para desarrollo fuera de contenedores: uv, just, Node.js y pnpm.
- Credenciales externas para probar BAW, Appian, Gemini y ngrok.

## Arranque con Docker Compose

1. Clona el repositorio y entra en la carpeta raíz.
2. Crea un archivo .env local a partir de .env.example si está disponible.
3. Completa las variables requeridas; no subas .env ni credenciales al repositorio.
4. Arranca los servicios:

    docker compose up -d --build
    docker compose ps

La interfaz local se sirve en http://localhost:8081. Ejemplos de comprobación por el proxy:

    curl -sS http://localhost:8081/api/expenses/
    curl -sS http://localhost:8081/api/monitor/overview

Para consultar logs:

    docker compose logs -f backend
    docker compose logs -f ngrok

Para detener los servicios y conservar los datos de PostgreSQL:

    docker compose down

No uses docker compose down -v salvo que quieras borrar el volumen y los datos persistidos.

## Variables de entorno

Los nombres deben coincidir con docker-compose.yml y con la configuración efectiva del backend. Variables utilizadas por el proyecto:

| Variable | Uso |
|---|---|
| DATABASE_URL | URL SQLAlchemy de PostgreSQL. En Compose, el host es el nombre del servicio de base de datos. |
| APPIAN_BASE_URL | URL base de Appian. |
| APPIAN_API_KEY | Clave que envía FastAPI al Web API de Appian. |
| BAW_BASE_URL | URL base del servidor BAW. |
| BAW_USER, BAW_PASSWORD | Credenciales de BAW para el backend. |
| BAW_BPD_ID, BAW_PROCESS_APP_ID | Identificadores de proceso y aplicación BAW. |
| BAW_CA_BUNDLE | Ruta al certificado CA si el servidor requiere un certificado específico. |
| BAW_ALLOW_LEGACY_CERTS | Compatibilidad temporal con el certificado legacy del entorno formativo. |
| GEMINI_API_KEY | Clave para OCR y chatbot. |
| DEMO_EMPLOYEE | Identidad simulada del empleado; por defecto, empleado_007. |
| NGROK_AUTHTOKEN, DOMAIN | Token y dominio estático si los referencia Compose. |

Usa valores locales. Si una clave real se expone en terminales, capturas, mensajes o historial Git, revócala y crea otra.

## Rutas principales

Swagger describe los schemas y rutas disponibles. Las rutas principales, vistas a través del prefijo /api del proxy, son:

| Método | Ruta | Función |
|---|---|---|
| GET | /api/expenses/ | Lista gastos. |
| GET | /api/expenses/{gasto_id} | Devuelve un gasto. |
| POST | /api/expenses/ | Crea un gasto e intenta iniciar BAW. |
| POST | /api/extract-invoice | Extrae datos de una imagen o PDF. |
| POST | /api/chat/ | Chat con function calling. |
| GET | /api/monitor/overview | KPIs, series y estados unificados. |
| GET | /api/appian/expenses/{gasto_id}/decision-context | Contexto de decisión para Appian. |
| POST | /api/appian/expenses/{gasto_id}/decision | Guarda en Expensr la decisión Appian. |

El Web API de Appian usado en el monitor está configurado con la ruta /suite/webapi/expensrActiveInstances. 

## Pruebas y calidad

Desde expensr-backend:

    just check
    just test-cov


Desde expensr-frontend:

    pnpm lint
    pnpm build


## Kubernetes local

El despliegue reportado usa el Kubernetes integrado de Docker Desktop, namespace expensr. Backend y frontend estaban 1/1, PostgreSQL 1/1 y el PVC enlazado. No hay Ingress; el acceso es mediante port-forward:

    kubectl config current-context
    kubectl get pods,deploy,statefulset,services,pvc -n expensr
    kubectl port-forward -n expensr service/expensr-frontend 8082:80

Con el port-forward activo, abre http://localhost:8082. ngrok se ejecuta desde Docker Compose fuera del cluster.

Los manifiestos están en k8s/ según el estado reportado. Revisa sus nombres y variables reales antes de aplicar en otro entorno. No guardes secretos reales en manifiestos versionados.

## Estructura del repositorio

    expensr-backend/      FastAPI, modelos, routers, servicios y tests
    expensr-frontend/     React + Vite
    k8s/                  Manifiestos Kubernetes
    docs/decisiones.md    Decisiones y excepciones autorizadas
    docker-compose.yml


## Limitaciones y cierre

- El login de empleado está simulado y no proporciona seguridad de producción.
- BAW/Appian no acceden directamente a PostgreSQL por JDBC; FastAPI intermedia,  documentada en docs/decisiones.md.
