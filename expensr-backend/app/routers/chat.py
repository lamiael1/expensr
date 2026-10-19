import logging
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

client = genai.Client()  # lee GEMINI_API_KEY del entorno
MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = (
    "Eres el asistente de Expensr, una app de gestión de gastos. "
    "Responde siempre en español, de forma breve y concreta. "
    "Usa las funciones disponibles para consultar datos reales del empleado; "
    "nunca inventes importes, estados ni fechas. "
    "Si una función indica que no hay datos, dilo con naturalidad."
)


class ChatRequest(BaseModel):
    message: str
    empleado: str = "empleado_007"


class ChatResponse(BaseModel):
    response: str
    function_called: str | None = None


@router.post("/", response_model=ChatResponse)
async def ask_chat(
    request: Annotated[ChatRequest, Body()],
    db: Annotated[Session, Depends(get_db)],
):
    contents = [types.Content(role="user", parts=[types.Part(text=request.message)])]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=GEMINI_TOOLS,
    )

    try:
        first = client.models.generate_content(
            model=MODEL, contents=contents, config=config
        )
    except APIError:
        logger.exception("Error llamando a Gemini (primera pasada)")
        return ChatResponse(
            response="No he podido conectar con el asistente de IA. Inténtalo de nuevo en unos segundos.",
            function_called=None,
        )

    function_call = None
    for part in first.candidates[0].content.parts:
        if part.function_call:
            function_call = part.function_call
            break

    if function_call is None:
        return ChatResponse(response=first.text or "", function_called=None)

    function_name = function_call.name
    args = dict(function_call.args or {})

    impl = FUNCTION_IMPLEMENTATIONS.get(function_name)

    if impl is None:
        function_result = {"error": f"Función desconocida: {function_name}"}
    else:
        args.pop("empleado", None)  # guardarraíl: nunca lo decide el modelo
        try:
            function_result = impl(db=db, empleado=request.empleado, **args)
        except TypeError as exc:
            logger.warning("Argumentos inválidos para %s: %s", function_name, exc)
            function_result = {"error": "Argumentos inválidos para la función."}

    contents.append(first.candidates[0].content)
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
        second = client.models.generate_content(
            model=MODEL, contents=contents, config=config
        )
    except APIError:
        logger.exception("Error llamando a Gemini (segunda pasada)")
        return ChatResponse(
            response="He consultado los datos pero no he podido redactar la respuesta. Inténtalo de nuevo.",
            function_called=function_name,
        )

    return ChatResponse(response=second.text or "", function_called=function_name)
