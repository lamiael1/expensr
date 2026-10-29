# Expensr - Sistema de Gestión e Integración de Gastos Empresariales

Expensr es una plataforma web end-to-end diseñada para el registro, validación operativa, evaluación financiera y monitoreo de gastos corporativos. El sistema orquesta flujos de trabajo entre una interfaz Single Page Application (SPA), un servidor API en Python, motores de procesos de negocio (IBM BAW y Appian), servicios de Inteligencia Artificial (OCR para facturas y chatbot interactivo) y una base de datos relacional PostgreSQL.

---

## Arquitectura y Tecnologías

El sistema se compone de varios módulos integrados mediante arquitecturas REST y comunicación asíncrona:

| Módulo | Tecnologías | Descripción |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts | Interfaz web con navegación mediante React Router y refresco dinámico de datos. |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2 | API REST central que orquesta la persistencia y la comunicación con servicios externos. |
| **Base de Datos** | PostgreSQL 16 | Persistencia relacional de gastos, presupuestos y trazabilidad de tiempos por etapa. |
| **BPM - Validación** | IBM Business Automation Workflow (BAW) | Flujo BPMN para autoinformado de centros de coste y tarea humana de revisión operativa. |
| **BPM - Decisión** | Appian | Evaluación de acumulados mensuales, reglas de negocio e interfaz SAIL de decisión final. |
| **Inteligencia Artificial** | OpenAI / Claude LLM | Servicio OCR de extracción estructurada de tickets y Chatbot con Function Calling. |
| **Contenerización** | Docker, Docker Compose, Nginx, Kubernetes | Empaquetado multietapa y manifiestos de despliegue local (k8s). |

---

## Estructura del Proyecto

```text
ProyectoExpensr/
├── expensr-backend/      Servidor FastAPI, routers, modelos Pydantic, servicios y tests
├── expensr-frontend/     Aplicación cliente React compilada con Vite y servida con Nginx
├── exports/              Exportables de los procesos BPM (BAW .twx y Appian .zip)
├── docs/                 Documentación técnica, arquitectura, base de datos y decisiones
├── k8s/                  Manifiestos de Kubernetes (PostgreSQL, Backend, Frontend)
└── docker-compose.yml    Configuración de orquestación de contenedores en desarrollo
```

---

## Despliegue con Docker Compose

El proyecto está configurado para ejecutarse en contenedores mediante Docker Compose con redes internas y volúmenes persistentes.

### 1. Variables de entorno

Copia y configura los archivos de entorno en la raíz y en el directorio del backend:

```bash
cp expensr-backend/.env.example expensr-backend/.env
```

### 2. Construcción e inicio

Ejecuta el siguiente comando para construir las imágenes e iniciar los servicios en segundo plano:

```bash
docker compose up -d --build
```

### 3. Puntos de acceso

Una vez iniciados los contenedores, los servicios están disponibles en los siguientes puertos:

| Servicio | URL / Puerto | Descripción |
| :--- | :--- | :--- |
| **Frontend Web** | `http://localhost:8081` | Aplicación web servida con Nginx |
| **Pestaña Monitoreo** | `http://localhost:8081/monitor` | Vista unificada de métricas y procesos |
| **Documentación API** | `http://localhost:8000/docs` | Swagger UI interactivo de FastAPI |
| **PostgreSQL** | `localhost:5432` | Base de datos (`expensr_db` / `expensr_user`) |

---

## Desarrollo Local (Sin Docker)

Para ejecutar el entorno de desarrollo local paso a paso:

### Backend (FastAPI)

```bash
cd expensr-backend
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend (React + Vite)

```bash
cd expensr-frontend
pnpm install
pnpm dev
```

Acceso al cliente de desarrollo: `http://localhost:5173`

---

## Despliegue en Kubernetes Local (Minikube / Kind)

Los manifiestos en el directorio `k8s/` permiten desplegar la arquitectura completa en un cluster local de Kubernetes.

1. **Crear el namespace y configuraciones de la base de datos:**

   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/db-init-configmap.yaml
   ```

2. **Desplegar la base de datos y los microservicios:**

   ```bash
   kubectl apply -f k8s/postgres.yaml
   kubectl apply -f k8s/backend.yaml
   kubectl apply -f k8s/frontend.yaml
   ```

3. **Verificar el estado de las cargas de trabajo:**

   ```bash
   kubectl get pods -n expensr
   ```

---

## Calidad de Código y Pruebas

Para verificar el cumplimiento de reglas de estilo, formato y pasar la suite de pruebas unitarias e integración en el backend:

```bash
cd expensr-backend
uv run ruff format --check .
uv run ruff check .
uv run pytest -v
```
