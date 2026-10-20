# Base de datos — contrato de integración

La base de datos PostgreSQL es el estado compartido entre tres sistemas:
el backend Python (FastAPI), IBM BAW y Appian. Cada sistema solo escribe
las columnas que le corresponden; el resto las lee.

El esquema está versionado en `expensr-backend/sql/001_create_schema.sql`
y los datos de ejemplo en `expensr-backend/sql/002_seed.sql`.

## Tabla `gastos`

### Escritas por el backend Python (al subir el gasto)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | BIGSERIAL | Clave primaria |
| `empleado` | VARCHAR(100) | Empleado autenticado |
| `fecha` | DATE | Fecha del gasto |
| `concepto` | VARCHAR(255) | Descripción breve |
| `categoria` | VARCHAR(100) | Dietas, Transporte, Material, Formacion |
| `importe` | NUMERIC(10,2) | Mayor o igual que 0 |
| `adjunto_url` | TEXT | Nombre o URL de la factura adjunta |
| `estado` | VARCHAR(50) | El backend lo inicia en `PENDIENTE_BAW` |
| `fecha_creacion` | TIMESTAMPTZ | Primer timestamp del flujo |

### Escritas por IBM BAW (vía `PATCH /baw/expenses/{id}/...`)

| Columna | Tipo | Notas |
|---|---|---|
| `centro_coste` | VARCHAR(100) | Autoinformado por regla de negocio (Dietas → `CC-COMERCIAL-01`) |
| `requiere_revision_manager` | BOOLEAN | Autoinformado (Dietas con importe mayor que 30 €) |
| `estado` | VARCHAR(50) | BAW lo actualiza al validar y al decidir |
| `comentario_baw` | TEXT | Comentario del revisor humano |
| `fecha_validacion_baw` | TIMESTAMPTZ | Segundo timestamp del flujo |

BAW no escribe directamente en la base de datos por JDBC: llama a los
endpoints `/baw/expenses/{id}/validation` y `/baw/expenses/{id}/decision`
del backend (ver `docs/decisiones.md`).

### Escritas por Appian (al cerrar el proceso)

| Columna | Tipo | Notas |
|---|---|---|
| `acumulado_mes` | NUMERIC(10,2) | Suma de gastos aprobados del empleado en la categoría durante el mes |
| `presupuesto_restante` | NUMERIC(10,2) | Límite mensual menos `acumulado_mes` |
| `decision_final` | VARCHAR(50) | Aprobar, Aprobar con ajuste o Rechazar |
| `comentario_appian` | TEXT | Comentario de Finanzas |
| `fecha_decision_appian` | TIMESTAMPTZ | Tercer timestamp del flujo |

## Tabla `presupuestos`

Límite mensual por empleado y categoría. Solo se lee (Appian y el
chatbot); se carga con los datos semilla.

| Columna | Tipo | Notas |
|---|---|---|
| `id` | BIGSERIAL | Clave primaria |
| `empleado` | VARCHAR(100) | |
| `categoria` | VARCHAR(100) | |
| `limite_mensual` | NUMERIC(10,2) | Mayor o igual que 0 |

Restricción: un único presupuesto por (`empleado`, `categoria`).

## Tiempos por etapa

Los tres timestamps permiten calcular la duración de cada etapa:

- Tiempo en BAW = `fecha_validacion_baw - fecha_creacion`
- Tiempo en Appian = `fecha_decision_appian - fecha_validacion_baw`
- Tiempo total = `fecha_decision_appian - fecha_creacion`

La pestaña de monitoreo y la función `tiempo_medio_aprobacion` del
chatbot se apoyan en ellos.
