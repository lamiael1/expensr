# Decisiones técnicas — Expensr

Este documento registra las decisiones técnicas, el estado de las integraciones y las limitaciones conocidas del proyecto.

## Frontend y backend

- El frontend es una SPA construida con React y Vite. React Router gestiona las vistas de subida de facturas, histórico de gastos, chatbot y monitoreo.
- FastAPI es el intermediario entre la interfaz, PostgreSQL, BAW, Appian y Gemini.
- El frontend no almacena ni recibe credenciales de BAW, Appian o Gemini.
- Nginx sirve el frontend y reenvía las peticiones de la interfaz bajo `/api/` al backend. También publica las rutas HTTP que necesitan las integraciones de BAW.

## Base de datos

Se utiliza PostgreSQL. El esquema y los datos de ejemplo están versionados en `expensr-backend/sql/`.

La tabla `gastos` contiene los datos de la factura, los campos de validación de BAW, la decisión de Appian y las fechas de trazabilidad. La tabla `presupuestos` guarda el límite mensual por empleado y categoría.

FastAPI administra las escrituras en la base de datos. BAW y Appian se comunican con FastAPI por HTTP, y el backend persiste sus cambios.

## Integración con IBM BAW

FastAPI inicia el proceso `ExpenseValidation` mediante la Process REST API de BAW. El identificador de instancia se guarda en el gasto y se devuelve al frontend.

BAW aplica las reglas de validación y comunica el centro de coste, la necesidad de revisión y el resultado al backend mediante HTTP. FastAPI actualiza PostgreSQL.

### Decisión de no usar JDBC desde BAW

El enunciado propone una integración SQL/JDBC desde BAW. Tras consultarlo, los tutores confirmaron que el proyecto puede resolverse sin JDBC. Por eso, BAW no se conecta directamente a PostgreSQL: invoca los endpoints HTTP de FastAPI, que centraliza las escrituras en la base de datos.

Esta decisión reduce la configuración de infraestructura y mantiene una única capa responsable de persistir los cambios. La contrapartida es que BAW depende de que el backend esté disponible para actualizar el gasto.

## Integración con Appian

El proceso financiero de Appian obtiene el contexto del gasto desde Expensr y envía la decisión final al backend mediante HTTP. FastAPI guarda la decisión, el comentario y las fechas correspondientes en PostgreSQL.

La decisión del gasto #19 se probó: el backend respondió `200 OK`, el gasto pasó a `APROBADO` y el monitor lo mostró como finalizado.

El informe de procesos activos y el Web API de Appian para el monitor están configurados. El backend tiene el adaptador para consumir el endpoint `expensrActiveInstances`; la consulta en vivo desde Expensr requiere `APPIAN_BASE_URL` y `APPIAN_API_KEY` en el `.env` local.

## Login simulado

El login actual identifica al empleado de demostración en el frontend. Los tutores confirmaron que se permite simular el login para este proyecto.

No es un mecanismo de autenticación de producción: el backend no valida una identidad real ni tokens de sesión. Las funciones del chatbot filtran por el empleado configurado por la aplicación, pero esto no sustituye la autenticación real.

## Inteligencia artificial

Se utiliza Gemini mediante el SDK `google-genai` para OCR de facturas y chatbot.

El OCR procesa imágenes o PDF, solicita datos estructurados y valida la respuesta antes de devolverla al frontend. El chatbot usa function calling con funciones limitadas para consultar gastos, estados y tiempos; no permite generar SQL libre.

La clave de Gemini se configura en el `.env` y no se incluye en el repositorio.

## Monitoreo

La pantalla de monitoreo presenta KPIs, tiempos por etapa, instancias recientes y actualización periódica. El backend consulta las fuentes externas y agrega sus resultados con los datos de PostgreSQL.

BAW se ha observado como fuente configurada y operativa. Appian dispone de un Web API y de un parser en el backend; la verificación de la consulta en vivo queda pendiente de configurar la API key.

## ngrok

ngrok expone el entorno local a BAW y Appian mediante el dominio estático reservado. En Docker Compose expone nginx, que sirve el frontend y reenvía las rutas correspondientes al backend.

El dominio y las claves se configuran fuera del código. El túnel debe permanecer activo mientras los sistemas externos necesiten llamar a Expensr.

## Docker Compose y Kubernetes

Docker Compose levanta frontend nginx, backend FastAPI y PostgreSQL. PostgreSQL utiliza un volumen persistente.

El despliegue Kubernetes local se comprobó en Docker Desktop: frontend, backend y PostgreSQL quedaron en estado `Running`, el PVC quedó `Bound` y la API respondió mediante `port-forward`.

El enunciado menciona Minikube o Kind. Se ha comunicado a los tutores que se utilizó Docker Desktop; la aceptación de esta diferencia depende de su confirmación.

## Pruebas y calidad

El backend dispone de pruebas automatizadas y comprobaciones Ruff ejecutadas mediante `just check`. Se han registrado 31 pruebas superadas.

El flujo BAW se ha probado creando instancias y completando tareas. La decisión Appian del gasto #19 se persistió y se reflejó en Expensr. La consulta de instancias Appian desde el monitor requiere la API key.

## Entorno y secretos

Los archivos `.env` se excluyen del repositorio. Las claves, contraseñas y credenciales se configuran localmente o mediante Secrets de Kubernetes.

No se deben incluir secretos en commits, capturas ni mensajes.
