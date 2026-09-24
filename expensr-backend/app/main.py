from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.routers import chat, expenses, monitor

# Crea las tablas en expensr.db al iniciar la aplicación
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expensr API",
    description="API de backend para la gestión de gastos empresarial",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expenses.router)
app.include_router(chat.router)
app.include_router(monitor.router)


@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Expensr"}
