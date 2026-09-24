from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import expenses

app = FastAPI(
    title="Expensr API",
    description="Backend para la gestión de notas de gastos",
    version="0.1.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectar los routers de la aplicación
app.include_router(expenses.router)


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "¡Backend de Expensr funcionando correctamente en WSL!",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
