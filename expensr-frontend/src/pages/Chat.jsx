import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { sendChatMessage } from '../services/api';

const CHAT_STORAGE_KEY = 'expensr_chat_messages';

const INITIAL_MESSAGES = [
  {
    sender: 'assistant',
    text: '¡Hola! Soy el asistente de Expensr. Pregúntame sobre tus gastos o estados pendientes.',
  },
];

const markdownComponents = {
  p: ({ children }) => (
    <p className="whitespace-pre-wrap">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold">{children}</strong>
  ),
  ol: ({ children }) => (
    <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>
  ),
  ul: ({ children }) => (
    <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>
  ),
  li: ({ children }) => <li>{children}</li>,
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
          ['user', 'assistant'].includes(message.sender) &&
          typeof message.text === 'string',
      );

    return validMessages ? parsedMessages : INITIAL_MESSAGES;
  } catch {
    return INITIAL_MESSAGES;
  }
}

function Chat() {
  const [messages, setMessages] = useState(getInitialMessages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    try {
      sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
    } catch (error) {
      console.warn(
        'No se pudo guardar el historial del chat en esta sesión.',
        error,
      );
    }
  }, [messages]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!input.trim() || loading) {
      return;
    }

    const userMessage = input.trim();
    setInput('');

    setMessages((previousMessages) => [
      ...previousMessages,
      { sender: 'user', text: userMessage },
    ]);

    setLoading(true);

    try {
      const storedUser = JSON.parse(localStorage.getItem('expensr_user') || '{}');
      const data = await sendChatMessage(
        userMessage,
        storedUser.empleado || 'empleado_007',
      );

      setMessages((previousMessages) => [
        ...previousMessages,
        {
          sender: 'assistant',
          text: data.response || 'El asistente no devolvió una respuesta.',
        },
      ]);
    } catch (error) {
      console.error('Error al enviar el mensaje al chatbot:', error);

      setMessages((previousMessages) => [
        ...previousMessages,
        {
          sender: 'assistant',
          text: `No he podido obtener respuesta: ${
            error instanceof Error ? error.message : 'error desconocido'
          }`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100vh-7rem)] max-w-4xl flex-col rounded-lg bg-white p-4 shadow-md">
      <div className="mb-4 border-b pb-3">
        <h2 className="text-xl font-semibold text-gray-800">
          Asistente Virtual - Expensr
        </h2>
        <p className="text-sm text-gray-500">
          Consulta información de gastos y estados conectados al sistema.
        </p>
      </div>

      <div className="mb-4 flex-1 space-y-4 overflow-y-auto rounded-lg bg-gray-50 p-4">
        {messages.map((message, index) => (
          <div
            key={`${message.sender}-${index}`}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[75%] rounded-lg p-3 text-sm ${
                message.sender === 'user'
                  ? 'rounded-br-none bg-blue-600 text-white'
                  : 'rounded-bl-none border border-gray-200 bg-white text-gray-800 shadow-sm'
              }`}
            >
              {message.sender === 'assistant' ? (
                <ReactMarkdown components={markdownComponents}>
                  {message.text}
                </ReactMarkdown>
              ) : (
                message.text
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-lg border border-gray-200 bg-white p-3 text-sm italic text-gray-500 shadow-sm">
              Pensando respuesta...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Escribe tu mensaje (ej. '¿Cuánto tengo en gastos?' o 'estado')..."
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}

export default Chat;
