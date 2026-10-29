# Expensr - Sistema de Gestión e Integración de Gastos Empresariales

Expensr es una aplicación web para la gestión, validación, evaluación financiera y monitoreo de gastos corporativos. El sistema orquesta procesos entre una interfaz web moderna, un backend en Python, motores de BPM (IBM BAW y Appian), servicios de Inteligencia Artificial para OCR y chatbot, y una base de datos relacional PostgreSQL.

## Arquitectura General

- Frontend: React 18, Vite, Tailwind CSS, Recharts.
- Backend: Python (FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn).
- Base de Datos: PostgreSQL 16.
- Motores BPM: IBM Business Automation Workflow (BAW) y Appian.
- Inteligencia Artificial: OCR para extracción de datos de facturas y Chatbot interactivo con Function Calling.
- Despliegue: Docker, Docker Compose y manifiestos de Kubernetes en k8s/.

## Estructura del Repositorio

expensr-backend/      Servidor FastAPI, routers, modelos y suite de tests con pytest
expensr-frontend/     Aplicación cliente React con Vite y Nginx
exports/              Exportaciones de los procesos BPM (BAW .twx y Appian .zip)
docs/                 Documentación de arquitectura, base de datos y decisiones de diseño
k8s/                  Manifiestos de Kubernetes para PostgreSQL, backend y frontend
docker-compose.yml    Configuración de contenedores para desarrollo y despliegue local

## Despliegue con Docker Compose

1. Configuración de variables de entorno:
   Asegúrate de tener los archivos .env configurados en la raíz y en expensr-backend/ según los archivos .env.example.

2. Iniciar el entorno:
   Ejecuta el siguiente comando para construir y levantar los contenedores:

   docker compose up -d --build

3. Puertos y accesos:
   - Frontend Web (Nginx): http://localhost:8081
   - Pestaña de Monitoreo: http://localhost:8081/monitor
   - Backend API / Documentación Swagger: http://localhost:8000/docs
   - Base de Datos PostgreSQL: localhost:5432 (Base de datos: expensr_db, Usuario: expensr_user)

## Desarrollo Local (Sin Docker)

Si prefieres ejecutar el frontend y backend de forma independiente durante el desarrollo:

1. Backend:
   cd expensr-backend
   uv run uvicorn app.main:app --reload --port 8000

2. Frontend:
   cd expensr-frontend
   pnpm install
   pnpm dev
   Acceso en desarrollo: http://localhost:5173

## Despliegue en Kubernetes Local (Minikube / Kind)

Para desplegar la aplicación en un cluster local de Kubernetes usando los manifiestos incluidos:

1. Aplicar el namespace y configuraciones:
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/db-init-configmap.yaml

2. Desplegar servicios:
   kubectl apply -f k8s/postgres.yaml
   kubectl apply -f k8s/backend.yaml
   kubectl apply -f k8s/frontend.yaml

3. Verificar los pods:
   kubectl get pods -n expensr

## Pruebas y Calidad de Código

Para verificar el formato, linters y pasar los tests del backend:

cd expensr-backend
uv run ruff format --check .
uv run ruff check .
uv run pytest -v
