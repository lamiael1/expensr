# Registro de Decisiones de Arquitectura (ADR) - Expensr

## 1. Arquitectura de Integración Asíncrona mediante Webhooks
* **Contexto:** Las plataformas BPM (IBM BAW y Appian) ejecutan tareas que requieren tiempo variable (revisiones humanas o evaluación de reglas de negocio).
* **Decisión:** Implementar comunicación asíncrona desacoplada mediante Callbacks HTTP (Webhooks). FastAPI expone endpoints dedicados (`/baw/callback`, `/appian/callback`) expuestos mediante túneles ngrok para entornos de desarrollo local.
* **Consecuencias:** Permite que la UI no quede bloqueada esperando respuestas síncronas de los motores BPM.

## 2. Estrategia de Fallback en el Módulo de Monitoreo
* **Contexto:** Las consultas REST a BAW y Appian pueden sufrir latencias o indisponibilidades parciales en entornos de desarrollo/red.
* **Decisión:** Implementar la función `fetch_all()` con `asyncio.gather(return_exceptions=True)` y manejo de degradación suave (*graceful degradation*).
* **Consecuencias:** Si un motor BPM no responde, la interfaz de monitoreo continúa sirviendo los datos almacenados en PostgreSQL mostrando un aviso de datos parciales al usuario.

## 3. Modelo de Persistencia Compartida en PostgreSQL
* **Contexto:** Se requiere un repositorio unificado para el seguimiento de los gastos y métricas de SLA sin depender exclusivamente de los historiales internos de BAW y Appian.
* **Decisión:** Centralizar el estado transaccional en la tabla `expenses` de PostgreSQL, utilizando SQLAlchemy 2.0 en el backend.

## 4. Contenerización y Orquestación Multi-Entorno
* **Contexto:** Garantizar paridad entre los entornos de desarrollo local y despliegue local simplificado.
* **Decisión:** Crear construcciones multietapa (*multi-stage build*) con Docker/Nginx para el frontend en React y FastAPI/Uvicorn para el backend, además de manifiestos YAML para Kubernetes (Kind/Minikube).
