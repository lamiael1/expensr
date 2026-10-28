# Decisiones técnicas de Expensr


Este documento explica las elecciones y adaptaciones técnicas de Expensr. 

## 1. Arquitectura

Expensr consta de una SPA React + Vite, backend FastAPI, PostgreSQL, procesos IBM BAW y Appian, IA generativa y despliegue local en Docker/Kubernetes. FastAPI sirve al frontend y hace de intermediario con los sistemas externos. El navegador no debe recibir credenciales de BAW, Appian, Gemini o ngrok.

Flujo previsto:

1. El empleado aporta una factura; el backend extrae sus datos y el empleado los revisa.
2. FastAPI crea el gasto en PostgreSQL e intenta iniciar el proceso de validación BAW.
3. BAW aplica reglas operativas y permite la revisión humana.
4. Appian calcula y presenta la decisión financiera.
5. Appian devuelve la decisión al endpoint de Expensr y el monitor consulta ambas plataformas mediante FastAPI.

El callback Appian → Expensr se probó: HTTP 200, gasto actualizado a aprobado y mostrado como finalizado. BAW estaba en mantenimiento en la última revisión, por lo que el flujo completo debe volver a probarse cuando se restablezca.

## 2. Tecnologías elegidas

| Área | Decisión | Razón |
|---|---|---|
| Interfaz | React + Vite | SPA por componentes, navegación y compilación estática servida por Nginx. |
| API | FastAPI + Pydantic | Tipado, validación de entrada/salida y documentación OpenAPI. |
| Persistencia | PostgreSQL + SQLAlchemy | Base relacional persistente para gastos y presupuestos. |
| Integración HTTP | HTTPX | Cliente HTTP para BAW/Appian; permite consultar fuentes de monitor en paralelo. |
| OCR/chat | Gemini gemini-3.5-flash-lite | Un proveedor cubre visión y function calling. La respuesta OCR se valida antes de usarse. |
| Exposición local | ngrok con dominio reservado | URL estable para callbacks externos y arranque mediante Compose. |
| Contenedores | Docker Compose | Arranque conjunto de frontend, backend, PostgreSQL y ngrok. |
| Orquestación local | Kubernetes integrado de Docker Desktop | Cluster disponible en el equipo para practicar namespace, Pods, Deployments, Services, PVC y kubectl. |

## 3. Excepciones acordadas con los tutores

### 3.1 Sin JDBC directo desde BAW/Appian

**Decisión:** no configurar datasource JDBC de BAW ni conexión directa Appian–PostgreSQL.

**Motivo:** los tutores autorizaron omitir JDBC si se explica la decisión. Configurar conectividad JDBC requiere coordinación del servidor y no es necesaria para demostrar el flujo de integración por APIs.

**Alternativa implementada:** PostgreSQL es gestionado por FastAPI. Appian obtiene el contexto de decisión por HTTP y devuelve el resultado con POST /api/appian/expenses/{gasto_id}/decision. BAW se integra con el backend y Appian por REST.

**Consecuencia:** la base de datos no es accedida directamente por los tres motores; FastAPI media y es responsable de mantener consistencia. Esta arquitectura difiere del objetivo didáctico de demostrar un Data Store compartido y debe explicarse en la presentación.

### 3.2 Login simulado

**Decisión:** usar una identidad de demostración configurable, en vez de implementar autenticación real.

**Motivo:** los tutores autorizaron simular el login.

**Implementación y guardarraíl:** DEMO_EMPLOYEE define la identidad usada por las funciones del chatbot (por defecto, empleado_007). El backend pasa esa identidad a las funciones; el modelo no puede cambiarla mediante argumentos.

**Consecuencia:** no hay autenticación, sesión real ni aislamiento multiusuario suficiente para producción. Esta configuración solo sirve para el prototipo formativo.

## 4. Adaptaciones adicionales

### 4.1 Gemini como proveedor de IA

El enunciado cita Claude u OpenAI como proveedores. Se eligió Gemini para usar visión/OCR y function calling en la misma integración. La clave se obtiene del entorno; Pydantic valida datos extraídos y los fallos del proveedor/formato se manejan con errores controlados.

Es una sustitución del proveedor sugerido. Se registra para que el tutor valore la equivalencia funcional; no debe presentarse como Claude/OpenAI.

### 4.2 Kubernetes de Docker Desktop

Se usa el cluster local docker-desktop en vez de Minikube o Kind porque ya está disponible y permite desplegar los servicios requeridos. El frontend se expone mediante kubectl port-forward. No hay Ingress, que es opcional en el enunciado. La elección se justifica por el objetivo de familiarización con Kubernetes, no por una arquitectura de producción.

### 4.3 ngrok integrado en Compose

ngrok se ejecuta como servicio con reinicio automático y dominio estático. El túnel apunta al Nginx del frontend, que enruta /api a FastAPI. Esto permite callbacks externos sin iniciar ngrok manualmente. El token y dominio se configuran localmente; no se escriben en este documento.

### 4.4 Monitor tolerante a fallos

GET /api/monitor/overview consulta BAW y Appian en paralelo y devuelve la disponibilidad/error de cada fuente. Si una no responde, la aplicación conserva los datos de la otra y puede mostrar el aviso. Las pruebas automatizadas simulan las fuentes externas; hace falta una prueba real cuando estén disponibles.

### 4.5 PostgreSQL y contrato de datos

Se usa PostgreSQL en vez de SQLite por persistencia y por el carácter relacional de la solución. El backend gestiona el acceso de aplicación. Las decisiones y transiciones de BAW/Appian regresan por HTTP al backend debido a la excepción de JDBC. El esquema SQL debe permanecer versionado y la documentación debe indicar qué componente actualiza cada campo.

## 5. Seguridad y operación

- No versionar .env, API keys, contraseñas ni tokens.
- No incluir credenciales en React, el bundle web, capturas o logs públicos.
- Rotar cualquier secreto que se haya expuesto en una conversación, consola compartida o historial Git.
- BAW_ALLOW_LEGACY_CERTS permite compatibilidad con el certificado legacy del entorno de formación. Mantenerlo limitado al entorno requerido.
- El login simulado y el uso de un túnel público no constituyen controles de producción.
- No ejecutar docker compose down -v si se desea conservar los datos de PostgreSQL.
