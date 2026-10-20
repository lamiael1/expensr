import { useState } from 'react';
import { sendChatMessage } from '../services/api';

function Chat() {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: '¡Hola! Soy el asistente de Expensr. Pregúntame sobre tus gastos o estados pendientes.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMessage }]);
    setLoading(true);

    const storedUser = JSON.parse(localStorage.getItem('expensr_user') || '{}');

    try {
      const data = await sendChatMessage(
        userMessage,
        storedUser.empleado || 'empleado_007',
      );
      setMessages((prev) => [...prev, { sender: 'assistant', text: data.response }]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { sender: 'assistant', text: 'Lo siento, no he podido conectar con el backend de FastAPI.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] max-w-4xl mx-auto p-4 bg-white rounded-lg shadow-md">
      <div className="mb-4 border-b pb-3">
        <h2 className="text-xl font-semibold text-gray-800">Asistente Virtual - Expensr</h2>
        <p className="text-sm text-gray-500">Consulta información de gastos y estados conectados al sistema.</p>
      </div>

      {/* Historial de mensajes */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-lg mb-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[75%] p-3 rounded-lg text-sm ${
                msg.sender === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none shadow-sm'
              }`}
            >
              {msg.text}
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

      {/* Formulario de entrada */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
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
