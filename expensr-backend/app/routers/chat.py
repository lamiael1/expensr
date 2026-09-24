from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/", response_model=ChatResponse)
async def ask_chat(request: Annotated[ChatRequest, Body()]):
    # Respuesta simulada (en la fase de IA se conectará con el LLM + RAG)
    user_msg = request.message.lower()

    if "gasto" in user_msg or "cuanto" in user_msg:
        reply = "Tienes 3 gastos registrados en el sistema por un total de 147.49 €."
    elif "estado" in user_msg or "pendiente" in user_msg:
        reply = "Hay 1 gasto pendiente de validación en IBM BAW."
    else:
        reply = f"Hola, he recibido tu mensaje: '{request.message}'. Soy el asistente de Expensr."

    return ChatResponse(reply=reply)
