from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, expenses, monitor

app = FastAPI(
    title="Expensr API",
    description="API de backend para la gestión de gastos empresarial",
    version="0.1.0",
)

# Configuración de CORS para conectar con el frontend en React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se especifica el dominio del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar los routers
app.include_router(expenses.router)
app.include_router(chat.router)
app.include_router(monitor.router)


@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Expensr"}
