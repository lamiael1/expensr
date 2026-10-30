# Base de datos

Expensr guarda sus gastos y presupuestos en PostgreSQL. FastAPI es el componente que lee y escribe estas tablas. BAW y Appian se integran con el backend por API; no acceden directamente a la base de datos por JDBC ni mediante un Data Store de Appian.

El esquema se define en `expensr-backend/sql/001_create_schema.sql`. Los datos iniciales se encuentran en `expensr-backend/sql/002_seed.sql`; Kubernetes tiene una copia de inicialización en `k8s/db-init-configmap.yaml`.

## Tabla `gastos`

| Columna | Tipo | Uso |
| --- | --- | --- |
| `id` | `BIGSERIAL` | Identificador del gasto |
| `empleado` | `VARCHAR(100)` | Empleado asociado al gasto |
| `fecha` | `DATE` | Fecha del gasto |
| `concepto` | `VARCHAR(255)` | Descripción breve |
| `categoria` | `VARCHAR(100)` | Categoría del gasto |
| `importe` | `NUMERIC(10,2)` | Importe, no negativo |
| `adjunto_url` | `TEXT` | Nombre o URL del justificante |
| `centro_coste` | `VARCHAR(100)` | Centro de coste informado durante la validación |
| `requiere_revision_manager` | `BOOLEAN` | Indica si requiere revisión de manager |
| `estado` | `VARCHAR(50)` | Estado actual del flujo |
| `comentario_baw` | `TEXT` | Comentario de revisión BAW |
| `fecha_validacion_baw` | `TIMESTAMPTZ` | Fecha de validación BAW |
| `baw_instance_id` | `VARCHAR(100)` | Identificador de instancia de BAW |
| `acumulado_mes` | `NUMERIC(10,2)` | Acumulado mensual usado en la decisión financiera |
| `presupuesto_restante` | `NUMERIC(10,2)` | Presupuesto restante calculado para la decisión |
| `decision_final` | `VARCHAR(50)` | Decisión financiera final |
| `comentario_appian` | `TEXT` | Comentario asociado a la decisión financiera |
| `fecha_decision_appian` | `TIMESTAMPTZ` | Fecha de la decisión financiera |
| `fecha_creacion` | `TIMESTAMPTZ` | Fecha de creación del registro |

Al crear un gasto, el backend lo guarda inicialmente con estado `PENDIENTE_BAW`. El backend intenta iniciar la instancia de BAW y guarda su identificador cuando recibe uno.

BAW actualiza los campos de validación y estado a través de los endpoints del backend `/baw/expenses/{gasto_id}/validation` y `/baw/expenses/{gasto_id}/decision`.

Appian obtiene los datos de decisión mediante `/appian/expenses/{gasto_id}/decision-context` y guarda el resultado mediante `/appian/expenses/{gasto_id}/decision`. El backend actualiza los campos financieros y el estado final.

## Tabla `presupuestos`

| Columna | Tipo | Uso |
| --- | --- | --- |
| `id` | `BIGSERIAL` | Identificador del presupuesto |
| `empleado` | `VARCHAR(100)` | Empleado al que se aplica |
| `categoria` | `VARCHAR(100)` | Categoría del presupuesto |
| `limite_mensual` | `NUMERIC(10,2)` | Límite mensual, no negativo |

La combinación de empleado y categoría es única. Los datos iniciales incluyen presupuestos de Dietas, Transporte, Material y Formación para el empleado de demostración.

## Cálculo de tiempos

Los campos de fecha permiten calcular las duraciones del flujo:

- Tiempo total en BAW: `fecha_validacion_baw - fecha_creacion`.
- Tiempo en Appian: `fecha_decision_appian - fecha_validacion_baw`.
- Tiempo total hasta la decisión: `fecha_decision_appian - fecha_creacion`.

El monitor usa esos datos para las métricas y la serie temporal. El chatbot también calcula el tiempo medio de resolución para el empleado configurado.

## Persistencia por entorno

Docker Compose guarda PostgreSQL en el volumen `postgres_data`. Kubernetes utiliza un PersistentVolumeClaim asociado al StatefulSet `expensr-postgres`. Son bases independientes y no sincronizan cambios automáticamente.
