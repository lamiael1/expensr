
# Decisiones técnicas — Expensr



## IA generativa: Gemini en vez de Claude/OpenAI



El enunciado especifica Claude u OpenAI para el chatbot y el OCR. Se optó por

Gemini (API con cuota gratuita, sin necesidad de dar datos de facturación)

por restricciones de presupuesto durante el programa formativo. Se probó

primero con OpenAI (bloqueado por falta de crédito) y se valoró Claude

(crédito de prueba gratuito disponible, pero se decidió priorizar una

opción sin fricción de facturación).



La arquitectura exigida por el enunciado se mantiene igual con Gemini:

patrón function calling, 3 funciones expuestas al modelo

(`listar_gastos`, `consultar_estado`, `tiempo_medio_aprobacion`), y

guardarraíl de seguridad — el parámetro `empleado` nunca lo decide el

modelo, siempre lo inyecta el backend a partir del usuario autenticado

en la request. Solo cambia el proveedor del modelo subyacente.



SDK usado: `google-genai` (el paquete unificado actual de Google;

`google-generativeai` está deprecado). Modelo: `gemini-3.8-flash`

(el anterior, `gemini-2.5-flash`, ya no está disponible para cuentas

nuevas en el momento de desarrollar este proyecto).



## Base de datos: PostgreSQL



Se eligió PostgreSQL (vía Docker, servicio `postgres` en

`docker-compose.yml`) en vez de SQLite, siguiendo la recomendación

explícita del enunciado de evitar SQLite por su peor encaje con BAW y

Appian. El esquema vive versionado en `expensr-backend/sql/` y se aplica

también mediante los modelos de SQLAlchemy en `app/models/expense_db.py`.



## Gestión de dependencias: uv



El backend usa `uv` (con `pyproject.toml` + `uv.lock`) en vez de

`requirements.txt`, por gestión de entornos virtuales más rápida y

reproducible.



## Autenticación: simulada en frontend



Por ahora el login (`Login.jsx`) valida contra credenciales fijas

(`empleado_007` / `expensr`) y guarda el usuario en `localStorage`,

sin backend de autenticación real. Es una simplificación deliberada

para esta fase del proyecto formativo — el empleado autenticado se

usa de forma consistente como guardarraíl en el chatbot y en la

creación de gastos, aunque el mecanismo de login en sí no sea

productivo.



## Pendiente de documentar



Esta lista se irá ampliando a medida que se tomen más decisiones

(BAW, Appian, ngrok, Docker, Kubernetes).

