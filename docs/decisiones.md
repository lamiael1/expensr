# Decisiones técnicas — Expensr

Este documento recoge las decisiones tomadas para implementar Expensr y las limitaciones que siguen pendientes. Se actualizará cuando se complete la integración con Appian.

## Frontend y backend

- El frontend es una SPA construida con React y Vite. React Router gestiona las rutas de subida de facturas, histórico de gastos, chatbot y monitoreo.
- FastAPI es el punto de entrada del backend y el proxy entre la interfaz, PostgreSQL y los sistemas externos. Las credenciales de BAW y Appian se mantienen en el backend.
- Nginx sirve el frontend y reenvía `/api/` al backend. También reenvía `/expenses/` y `/baw/` directamente al backend porque las operaciones REST configuradas en BAW llaman esas rutas sin el prefijo `/api`.

## Base de datos: PostgreSQL

Se utiliza PostgreSQL, en lugar de SQLite, para mantener un esquema relacional compartido y compatible con los requisitos de integración del proyecto. El esquema y los datos de ejemplo están versionados en `expensr-backend/sql/`.

La tabla `gastos` guarda los datos del gasto, los campos de validación BAW, los campos de decisión Appian y los timestamps del flujo. La tabla `presupuestos` contiene los límites mensuales por empleado y categoría.

Responsabilidad de escritura actual:

- **FastAPI** crea el gasto y asigna el estado inicial `PENDIENTE_BAW`.
- **BAW** comunica los datos de validación al backend mediante los endpoints `/baw/expenses/{gasto_id}/validation` y `/baw/expenses/{gasto_id}/decision`; el backend persiste los cambios.
- **Appian** debe calcular y guardar la decisión final, los importes acumulados y el timestamp correspondiente. Esta parte está pendiente de implementar y validar.

La integración de BAW con PostgreSQL se realiza actualmente a través del backend REST, no mediante una conexión JDBC directa desde BAW. Se eligió este flujo para que FastAPI sea el único componente que escriba en la base de datos. El enunciado menciona integración SQL desde BAW; esta diferencia debe confirmarse con el tutor y explicarse en la entrega.

## Integración con IBM BAW

FastAPI inicia el proceso `ExpenseValidation` mediante la Process REST API de BAW. El ID de instancia devuelto se guarda en `baw_instance_id` y se devuelve al frontend.

Los datos de entrada se envían usando los nombres de variables definidos en el proceso: `gasto_id`, `empleado`, `fecha`, `concepto`, `categoria`, `importe` y `adjunto_url`. BAW aplica las reglas de validación y llama a los endpoints del backend para registrar el resultado.

La interfaz de ngrok se configuró para recibir las llamadas de BAW a través de nginx. El túnel debe permanecer activo mientras BAW necesite comunicarse con el entorno local.

## Integración con Appian — pendiente

Appian debe recibir desde BAW los gastos validados, ejecutar el proceso de decisión financiera, calcular el acumulado mensual y el presupuesto restante, presentar una tarea de decisión a Finanzas y guardar el resultado.

El backend ya contiene configuración y adaptadores destinados a consultar el Web API `listActiveInstances` para monitoreo. La integración completa requiere crear y validar el proceso `ExpenseDecision`, el Record Type y Data Store, la interfaz SAIL y los Web APIs `startExpenseProcess` y `listActiveInstances`.

Las claves y las URL de Appian deben residir en `expensr-backend/.env` o en Secrets del entorno, nunca en el frontend.

## IA generativa: Gemini

Se utiliza el SDK `google-genai` y el modelo `gemini-3.5-flash-lite` para la extracción de datos de facturas y el chatbot. Se eligió Gemini por las restricciones de presupuesto del proyecto.

El OCR procesa imágenes o PDF, solicita una salida JSON estructurada y valida el resultado con Pydantic antes de devolverlo al frontend.

El chatbot usa function calling con un conjunto limitado de funciones (`listar_gastos`, `consultar_estado` y `tiempo_medio_aprobacion`). El modelo no genera SQL libre. El backend fija la identidad de demo para ejecutar las consultas; el login actual es simulado y no equivale a autenticación de producción.

## Túnel y rutas de red

Para Docker Compose, ngrok expone el puerto `8081` del frontend nginx. Así el navegador y las llamadas de BAW usan el mismo dominio. El frontend llama a la API a través de `/api/`; las operaciones BAW usan `/expenses/` y `/baw/`.

El dominio estático configurado es específico del entorno de desarrollo. Las credenciales y URL no deben codificarse en el JavaScript del frontend.

## Docker Compose y Kubernetes

Docker Compose levanta frontend nginx, backend FastAPI y PostgreSQL. PostgreSQL usa un volumen persistente.

Los manifiestos Kubernetes se encuentran en `k8s/`. El despliegue local se comprobó en el contexto Kubernetes de Docker Desktop: los pods de frontend, backend y PostgreSQL quedaron en `Running`, el PVC quedó `Bound` y la ruta `/api/expenses/` devolvió `200 OK`.

La base de datos de Kubernetes es independiente de la de Docker Compose; cada entorno tiene sus propios datos. El clúster comprobado es Docker Desktop. El enunciado especifica Minikube o Kind, por lo que la aceptación de Docker Desktop debe confirmarse con el tutor.

## Pruebas y calidad

El backend pasa Ruff y sus 31 pruebas automatizadas. La validación real de BAW se comprobó creando instancias y avanzando el flujo de validación. La decisión final de Appian y el despliegue en Minikube o Kind siguen pendientes de validación.

## Autenticación y secretos

El login del frontend es una simulación para la demo y guarda el usuario en `localStorage`; todavía no existe un sistema de autenticación real en FastAPI.

Los archivos `.env` se excluyen del repositorio. En Kubernetes, las credenciales se suministran mediante Secrets. No se deben incluir claves, contraseñas ni certificados privados en commits o capturas compartidas.
