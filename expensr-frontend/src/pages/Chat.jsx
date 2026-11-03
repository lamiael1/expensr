import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { sendChatMessage } from "../services/api";

const CHAT_STORAGE_KEY = "expensr_chat_messages";

const INITIAL_MESSAGES = [
  {
    sender: "assistant",
    text: "¡Hola! Soy el asistente de Expensr. Puedo ayudarte a consultar tus gastos y revisar su estado.",
  },
];

const SUGERENCIAS = [
  {
    titulo: "Estado de mis gastos",
    texto: "¿En qué estado están mis gastos?",
    icono: "◷",
  },
  {
    titulo: "Gasto más reciente",
    texto: "¿Cuál es el estado de mi gasto más reciente?",
    icono: "↗",
  },
  {
    titulo: "Gastos del mes",
    texto: "¿Cuánto he gastado este mes?",
    icono: "€",
  },
];

const markdownComponents = {
  p: ({ children }) => (
    <p className="whitespace-pre-wrap leading-7">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-gray-950">{children}</strong>
  ),
  ol: ({ children }) => (
    <ol className="my-3 list-decimal space-y-1.5 pl-5">{children}</ol>
  ),
  ul: ({ children }) => (
    <ul className="my-3 list-disc space-y-1.5 pl-5">{children}</ul>
  ),
  li: ({ children }) => <li className="pl-1">{children}</li>,
};

function getInitialMessages() {
  try {
    const storedMessages = sessionStorage.getItem(CHAT_STORAGE_KEY);

    if (!storedMessages) {
      return INITIAL_MESSAGES;
    }

    const parsedMessages = JSON.parse(storedMessages);
    const validMessages =
      Array.isArray(parsedMessages) &&
      parsedMessages.every(
        (message) =>
          ["user", "assistant"].includes(message.sender) &&
          typeof message.text === "string",
      );

    return validMessages && parsedMessages.length > 0
      ? parsedMessages
      : INITIAL_MESSAGES;
  } catch {
    return INITIAL_MESSAGES;
  }
}

function IconoAsistente({ pequeno = false }) {
  return (
    <span
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 font-bold text-white shadow-sm ${
        pequeno ? "h-8 w-8 text-sm" : "h-11 w-11 text-lg"
      }`}
    >
      E
    </span>
  );
}

function IndicadorEscritura() {
  return (
    <div
      className="flex items-center gap-1.5 rounded-2xl rounded-tl-md border border-gray-200 bg-white px-4 py-3 shadow-sm"
      role="status"
      aria-label="Expensr está preparando una respuesta"
    >
      <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:120ms]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:240ms]" />
      <span className="ml-2 text-xs text-gray-500">Preparando respuesta</span>
    </div>
  );
}

function Chat() {
  const [messages, setMessages] = useState(getInitialMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const conversationRef = useRef(null);
  const inputRef = useRef(null);
  const formRef = useRef(null);

  useEffect(() => {
    try {
      sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
    } catch (error) {
      console.warn(
        "No se pudo guardar el historial del chat en esta sesión.",
        error,
      );
    }
  }, [messages]);

  useEffect(() => {
    conversationRef.current?.scrollTo({
      top: conversationRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function enviarMensaje(texto) {
    const mensaje = texto.trim();

    if (!mensaje || loading) return;

    setInput("");
    setMessages((anteriores) => [
      ...anteriores,
      { sender: "user", text: mensaje },
    ]);
    setLoading(true);

    try {
      const storedUser = JSON.parse(localStorage.getItem("expensr_user") || "{}");
      const data = await sendChatMessage(
        mensaje,
        storedUser.empleado || "empleado_007",
      );

      setMessages((anteriores) => [
        ...anteriores,
        {
          sender: "assistant",
          text: data.response || "El asistente no devolvió una respuesta.",
        },
      ]);
    } catch (error) {
      console.error("Error al enviar el mensaje al chatbot:", error);

      setMessages((anteriores) => [
        ...anteriores,
        {
          sender: "assistant",
          text: `No he podido obtener respuesta: ${
            error instanceof Error ? error.message : "error desconocido"
          }`,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    void enviarMensaje(input);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      formRef.current?.requestSubmit();
    }
  }

  function limpiarConversacion() {
    if (loading) return;

    setMessages(INITIAL_MESSAGES);
    setInput("");
    inputRef.current?.focus();
  }

  const mostrarSugerencias = messages.length === 1 && !loading;

  return (
    <main className="mx-auto flex h-[calc(100vh-8rem)] min-h-[32rem] max-w-5xl flex-col overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-xl shadow-slate-200/60">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-100 bg-white px-5 py-4 sm:px-7">
        <div className="flex min-w-0 items-center gap-3">
          <IconoAsistente />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="truncate text-lg font-bold tracking-tight text-gray-950 sm:text-xl">
                Preguntar a Expensr
              </h1>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Disponible
              </span>
            </div>
            <p className="mt-0.5 text-sm text-gray-500">
              Consulta tus gastos y su estado en lenguaje natural.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={limpiarConversacion}
          disabled={loading || messages.length === 1}
          className="rounded-xl px-3 py-2 text-sm font-semibold text-gray-500 transition hover:bg-gray-100 hover:text-gray-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Limpiar conversación
        </button>
      </header>

      <section
        ref={conversationRef}
        className="flex-1 space-y-6 overflow-y-auto bg-gradient-to-b from-slate-50/80 to-white px-4 py-6 sm:px-8"
        aria-label="Conversación con el asistente"
        aria-live="polite"
        aria-relevant="additions"
      >
        {mostrarSugerencias && (
          <div className="mx-auto flex max-w-2xl flex-col items-center py-4 text-center sm:py-8">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-blue-100 to-indigo-100 text-3xl text-blue-700">
              ✦
            </div>
            <h2 className="text-xl font-bold tracking-tight text-gray-950 sm:text-2xl">
              ¿En qué puedo ayudarte?
            </h2>
            <p className="mt-2 max-w-lg text-sm leading-6 text-gray-500">
              Pregúntame por tus gastos, sus estados o el proceso de validación.
            </p>

            <div className="mt-7 grid w-full gap-3 text-left sm:grid-cols-3">
              {SUGERENCIAS.map((sugerencia) => (
                <button
                  key={sugerencia.titulo}
                  type="button"
                  onClick={() => void enviarMensaje(sugerencia.texto)}
                  className="group rounded-2xl border border-gray-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md disabled:cursor-wait"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-lg font-semibold text-blue-700 transition group-hover:bg-blue-100">
                    {sugerencia.icono}
                  </span>
                  <span className="mt-3 block text-sm font-semibold text-gray-800">
                    {sugerencia.titulo}
                  </span>
                  <span className="mt-1 block text-xs leading-5 text-gray-500">
                    {sugerencia.texto}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-5">
          {messages.map((message, index) => {
            const esUsuario = message.sender === "user";

            return (
              <div
                key={`${message.sender}-${index}`}
                className={`flex items-end gap-2.5 sm:gap-3 ${
                  esUsuario ? "justify-end" : "justify-start"
                }`}
              >
                {!esUsuario && <IconoAsistente pequeno />}

                <div
                  className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[75%] sm:px-5 ${
                    esUsuario
                      ? "rounded-br-md bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-900/10"
                      : "rounded-bl-md border border-gray-200 bg-white text-gray-700 shadow-sm"
                  }`}
                >
                  {esUsuario ? (
                    <p className="whitespace-pre-wrap">{message.text}</p>
                  ) : (
                    <ReactMarkdown components={markdownComponents}>
                      {message.text}
                    </ReactMarkdown>
                  )}
                </div>

                {esUsuario && (
                  <span
                    aria-hidden="true"
                    className="mb-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-xs font-bold text-slate-700"
                  >
                    Tú
                  </span>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex items-end gap-2.5 sm:gap-3">
              <IconoAsistente pequeno />
              <IndicadorEscritura />
            </div>
          )}
        </div>
      </section>

      <footer className="border-t border-gray-100 bg-white p-4 sm:px-6 sm:py-5">
        <form
          ref={formRef}
          onSubmit={handleSubmit}
          className="mx-auto flex max-w-4xl items-end gap-2 rounded-2xl border border-gray-200 bg-gray-50 p-2 transition focus-within:border-blue-300 focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-100"
        >
          <label className="sr-only" htmlFor="chat-message">
            Escribe tu pregunta
          </label>
          <textarea
            ref={inputRef}
            id="chat-message"
            rows={1}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu pregunta…"
            disabled={loading}
            className="max-h-32 min-h-11 flex-1 resize-y bg-transparent px-3 py-3 text-sm text-gray-900 outline-none placeholder:text-gray-400 disabled:cursor-wait"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="inline-flex h-11 shrink-0 items-center gap-2 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            <span>Enviar</span>
            <span aria-hidden="true">↑</span>
          </button>
        </form>
        <p className="mt-2 text-center text-xs text-gray-400">
          Intro para enviar · Mayús + Intro para escribir en otra línea
        </p>
      </footer>
    </main>
  );
}

export default Chat;
