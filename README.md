# Expensr

Aplicación de gestión de gastos empresariales con frontend React + Vite, backend FastAPI, PostgreSQL e integraciones con IBM BAW y Appian. Incluye extracción de datos de facturas con Gemini, chatbot y monitoreo.

## Requisitos

- Docker y Docker Compose.
- `uv` para desarrollo del backend.
- Node.js y `pnpm` para desarrollo del frontend.
- `kubectl` y un clúster Kubernetes local.
- ngrok para permitir llamadas desde BAW y Appian al entorno local.

## Configuración local

Docker Compose lee las credenciales de PostgreSQL desde `.env` en la raíz del proyecto. Si no existe, créalo con estos nombres de variables y valores locales:

```dotenv
POSTGRES_DB=expensr
POSTGRES_USER=expensr
POSTGRES_PASSWORD=cambia-esta-contraseña-local
