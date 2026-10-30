# Decisiones de arquitectura

## 1. Integración con BAW y Appian mediante API

BAW y Appian intercambian datos con Expensr mediante endpoints HTTP del backend. FastAPI es el punto de acceso a la base de datos. Los motores BPM no escriben directamente en PostgreSQL por JDBC ni mediante un Data Store de Appian.

El backend registra el gasto y trata de iniciar el proceso de BAW. Durante el flujo, BAW consulta los datos del gasto y envía al backend la validación o resolución. Appian puede consultar el contexto financiero y enviar la decisión final a Expensr.

En los despliegues locales, ngrok permite que los servicios BPM alojados fuera del equipo alcancen el frontend, que reenvía las rutas de API al backend. En Kubernetes, el manifiesto `k8s/ngrok.yaml` dirige el túnel al Service `expensr-frontend`.

**Consecuencia:** la interfaz no espera a que termine el proceso BPM para registrar el gasto. El estado del proceso se actualiza mediante llamadas posteriores a la API.

## 2. Degradación controlada del monitor

Las consultas de monitorización a BAW y Appian pueden fallar o tardar demasiado. El backend las ejecuta en paralelo con manejo de excepciones, de modo que un fallo de una fuente no impide devolver los datos locales de PostgreSQL.

**Consecuencia:** el monitor puede mostrar datos parciales y un aviso indicando qué fuente no responde.

## 3. PostgreSQL como persistencia de Expensr

El backend mantiene en PostgreSQL los gastos, presupuestos, decisiones y marcas de tiempo. BAW y Appian intercambian sus datos con el backend por API; no comparten una conexión SQL con la aplicación.

Docker Compose y Kubernetes usan persistencias independientes: Compose utiliza el volumen `postgres_data` y Kubernetes un volumen persistente asociado al StatefulSet `expensr-postgres`.

**Consecuencia:** los datos de un entorno no aparecen automáticamente en el otro. Para cambiar de entorno se debe usar el correspondiente despliegue y su base de datos.

## 4. Despliegue en Docker Compose y Kubernetes

El proyecto mantiene configuraciones para Docker Compose y Kubernetes. Ambos entornos ejecutan frontend, backend y PostgreSQL, pero cada uno tiene su propia red, configuración y almacenamiento persistente.

En Kubernetes, los manifiestos del directorio `k8s/` despliegan PostgreSQL, backend y frontend. El túnel de ngrok se despliega por separado con `k8s/ngrok.yaml` y requiere el Secret `ngrok-auth`.

**Consecuencia:** los manifiestos permiten probar el sistema en un clúster local sin convertir la base de Kubernetes en la misma base que usa Compose.

## 5. Appian sin acceso JDBC a PostgreSQL

La integración con Appian utiliza la API de Expensr para consultar el contexto de decisión y registrar el resultado. No se configura un Data Store de Appian conectado por JDBC porque el entorno no dispone de acceso JDBC a PostgreSQL.

**Consecuencia:** los datos de decisión se guardan en PostgreSQL a través del backend de Expensr.
