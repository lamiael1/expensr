import { useEffect, useState } from 'react';
import { sendChatMessage } from '../services/api';

const CHAT_STORAGE_KEY = 'expensr_chat_messages';

const INITIAL_MESSAGES = [
  {
    sender: 'assistant',
    text: '¡Hola! Soy el asistente de Expensr. Pregúntame sobre tus gastos o estados pendientes.',
  },
];

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
      console.warn('No se pudo guardar el historial del chat en esta sesión.', error);
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
    <div className="flex flex-col h-[calc(100vh-7rem)] max-w-4xl mx-auto p-4 bg-white rounded-lg shadow-md">
      <div className="mb-4 border-b pb-3">
        <h2 className="text-xl font-semibold text-gray-800">
          Asistente Virtual - Expensr
        </h2>
        <p className="text-sm text-gray-500">
          Consulta información de gastos y estados conectados al sistema.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-lg mb-4">
        {messages.map((message, index) => (
          <div
            key={`${message.sender}-${index}`}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[75%] p-3 rounded-lg text-sm ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none shadow-sm'
              }`}
            >
              {message.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-500 border border-gray-200 p-3 rounded-lg text-sm italic shadow-sm">
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
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}

export default Chat;
