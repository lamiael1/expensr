# Arquitectura del Sistema - Expensr

El sistema **Expensr** integra aplicaciones web, orquestación de procesos de negocio (BPM), inteligencia artificial y persistencia relacional en un entorno de microservicios contenerizados.

## Diagrama de Componentes y Flujo de Datos

```
+-----------------------------------------------------------------------------------+
|                                    Navegador                                      |
|                            [ React + Vite + Tailwind ]                            |
+-----------------------------------------------------------------------------------+
                                    |        ^
                       REST / HTTP  |        |  Respuesta UI
                                    v        |
+-----------------------------------------------------------------------------------+
|                                 Backend FastAPI                                   |
|                                                                                   |
|  +--------------------+  +--------------------+  +-----------------------------+  |
|  | /expenses /ocr     |  | /chat (LLM)        |  | /monitor                    |  |
|  | Routers Principales|  | Function Calling   |  | Métricas & SLA              |  |
|  +--------------------+  +--------------------+  +-----------------------------+  |
+-----------------------------------------------------------------------------------+
       |              |                |                     |
       | SQLAlchemy   | HTTP / REST    | REST                | REST (Consultas)
       v              v                v                     v
+------------+  +--------------+  +---------------+  +------------------------------+
| PostgreSQL |  |  Servicio    |  |    IBM BAW    |  |         Appian BPM           |
| (Database) |  | OCR / OpenAI |  | (Validación)  |  |  (Decisión & Reglas Nomb.)   |
+------------+  +--------------+  +---------------+  +------------------------------+
       ^                                 |                           |
       |            Callback Webhook     |     Callback Webhook      |
       +---------------------------------+---------------------------+
                        (A través de túnel HTTP ngrok)
```

## Flujo End-to-End del Proceso de Gasto

1. **Captura y OCR:** El usuario sube una factura/ticket desde el Frontend. El backend procesa la imagen a través del servicio OCR extrayendo datos estructurados (empleado, concepto, importe, fecha).
2. **Registro Inicial:** El gasto se almacena en PostgreSQL con estado `PENDIENTE_BAW`.
3. **Validación en IBM BAW:** El backend invoca la REST API de IBM BAW para iniciar la instancia del proceso de validación humana/administrativa.
4. **Webhook BAW:** Al finalizar la revisión en BAW, este notifica al backend vía webhook (exposición con ngrok en desarrollo local), actualizando el estado a `PENDIENTE_APPIAN` o `RECHAZADO_BAW`.
5. **Decisión Financiera en Appian:** Si BAW aprueba el gasto, el backend inicia el proceso en Appian para evaluar las reglas financieras e importe.
6. **Webhook Appian:** Appian procesa la decisión final y notifica al backend, actualizando el estado final (`APROBADO` / `RECHAZADO`).
7. **Monitoreo & Chatbot:** La pestaña de monitoreo consulta en tiempo real métricas y series temporales consolidadas de PostgreSQL, BAW y Appian. El chatbot permite consultar o crear gastos mediante la ejecución de funciones (*Function Calling*).
