# 💳 Expensr - Sistema de Gestión e Integración de Gastos Empresariales

**Expensr** es una plataforma integral para el registro, validación, evaluación financiera y monitoreo de gastos corporativos. Integra interfaces modernas en React, un orquestador central en FastAPI, automatización de procesos con **IBM Business Automation Workflow (BAW)** y **Appian**, lectura inteligente de facturas vía **OCR**, asistencia mediante un **Chatbot con Function Calling** y despliegues contenerizados en **Docker** y **Kubernetes**.

---

## 🚀 Arquitectura General

* **Frontend:** React + Vite, Tailwind CSS, Recharts.
* **Backend:** Python (FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn).
* **Base de Datos:** PostgreSQL 16.
* **Motores BPM:** IBM BAW v11.3 & Appian.
* **Inteligencia Artificial:** Servicio OCR de facturas y Chatbot interactivo (OpenAI / Function Calling).
* **Despliegue:** Docker Compose y manifiestos de Kubernetes (`k8s/`).

---

## 📁 Estructura del Repositorio

```text
ProyectoExpensr/
├── expensr-backend/      # Servidor FastAPI, routers, modelos y tests con pytest
├── expensr-frontend/     # Aplicación React + Vite + Tailwind CSS
├── exports/              # Exportaciones de los procesos BPM
│   ├── appian/          # Paquete de aplicación de Appian (.zip)
│   └── baw/             # Process App / Toolkit de IBM BAW (.twx)
├── docs/                 # Diagramas de arquitectura y decisiones de diseño
├── k8s/                  # Manifiestos de Kubernetes (PostgreSQL, Backend, Frontend)
└── docker-compose.yml    # Orquestación de contenedores locales
```

---

## 🛠️ Requisitos Previos

* Docker y Docker Compose
* Python >= 3.11 y `uv` (administrador de entornos y paquetes)
* Node.js y `pnpm`
* Cuenta/Túnel de **ngrok** configurado

---

## 💻 Ejecución con Docker Compose

1. **Configurar variables de entorno:**
   Copia los archivos de ejemplo `.env.example` a `.env` tanto en la raíz como en `expensr-backend/` e introduce tus credenciales y dominios de ngrok.

2. **Iniciar los servicios:**
   ```bash
   docker compose up -d --build
   ```

3. **Acceso a las aplicaciones:**
   * **Frontend Web:** [http://localhost:5173](http://localhost:5173) (o puerto mapeado en Nginx).
   * **Documentación API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ☸️ Despliegue en Kubernetes Local (Kind / Minikube)

Para desplegar la aplicación completa en Kubernetes:

1. **Crear el Namespace y ConfigMaps:**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/db-init-configmap.yaml
   ```

2. **Desplegar la Base de Datos:**
   ```bash
   kubectl apply -f k8s/postgres.yaml
   ```

3. **Desplegar Backend y Frontend:**
   ```bash
   kubectl apply -f k8s/backend.yaml
   kubectl apply -f k8s/frontend.yaml
   ```

4. **Verificar estado de los pods:**
   ```bash
   kubectl get pods -n expensr
   ```

---

## 🧪 Pruebas y Calidad de Código

Para ejecutar las comprobaciones de formato, linters y suite de pruebas unitarias/integración en el backend:

```bash
cd expensr-backend
uv run ruff format --check .
uv run ruff check .
uv run pytest -v
```
