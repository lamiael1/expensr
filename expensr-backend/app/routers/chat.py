import logging
import os
from typing import Annotated

from fastapi import APIRouter, Body, Depends
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.chat_functions import FUNCTION_IMPLEMENTATIONS, GEMINI_TOOLS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

DEMO_EMPLOYEE = os.getenv("DEMO_EMPLOYEE", "empleado_007")
GEMINI_MODEL = "gemini-3.5-flash-lite"

client = genai.Client(
    http_options=types.HttpOptions(
        timeout=15_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    )
)

SYSTEM_PROMPT = (
    "Eres el asistente de Expensr, una app de gestión de gastos. "
    "Responde siempre en español, de forma breve y concreta. "
    "Usa las funciones disponibles para consultar datos reales del empleado; "
    "nunca inventes importes, estados ni fechas. "
    "Si una función indica que no hay datos, dilo con naturalidad."
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    function_called: str | None = None


def _generate(contents, config):
    """Genera una respuesta usando Gemini 3.5 Flash Lite."""
    return client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=config,
    )


@router.post("/", response_model=ChatResponse)
async def ask_chat(
    request: Annotated[ChatRequest, Body()],
    db: Annotated[Session, Depends(get_db)],
):
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=request.message)],
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=GEMINI_TOOLS,
    )

    try:
        first = _generate(contents, config)
    except APIError:
        logger.exception("Error llamando a Gemini 3.5 Flash Lite")
        return ChatResponse(
            response=(
                "No he podido conectar con el asistente de IA. "
                "Inténtalo de nuevo en unos segundos."
            ),
            function_called=None,
        )

    candidate = first.candidates[0] if first.candidates else None
    parts = candidate.content.parts if candidate and candidate.content else None

    function_call = None
    if parts:
        for part in parts:
            if part.function_call:
                function_call = part.function_call
                break

    if function_call is None or not function_call.name:
        return ChatResponse(response=first.text or "", function_called=None)

    function_name = function_call.name
    args = dict(function_call.args or {})
    implementation = FUNCTION_IMPLEMENTATIONS.get(function_name)

    if implementation is None:
        function_result = {"error": f"Función desconocida: {function_name}"}
    else:
        args.pop("empleado", None)
        try:
            function_result = implementation(
                db=db,
                empleado=DEMO_EMPLOYEE,
                **args,
            )
        except TypeError as exc:
            logger.warning(
                "Argumentos inválidos para %s: %s",
                function_name,
                exc,
            )
            function_result = {
                "error": "Argumentos inválidos para la función."
            }

    if candidate and candidate.content:
        contents.append(candidate.content)

    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        name=function_name,
                        response={"result": function_result},
                    )
                )
            ],
        )
    )

    try:
        second = _generate(contents, config)
    except APIError:
        logger.exception(
            "Error en la segunda llamada a Gemini 3.5 Flash Lite"
        )
        return ChatResponse(
            response=(
                "He consultado los datos pero no he podido redactar "
                "la respuesta. Inténtalo de nuevo."
            ),
            function_called=function_name,
        )

    return ChatResponse(
        response=second.text or "",
        function_called=function_name,
    )
