import { useState } from "react";

const respuestasMock = [
  {
    id: 1,
    pregunta: "¿Qué me recomiendas para una fiesta?",
    respuesta:
      "¡Claro! Para una fiesta te sugiero un vestido midi en tonos vibrantes como rojo o rosa neón, combinado con accesorios dorados. Si prefieres pantalón, unos palazzo satinados con una blusa casual elegante son perfectos.",
  },
  {
    id: 2,
    pregunta: "¿Cómo combino este pantalón?",
    respuesta:
      "Ese pantalón queda genial con una camiseta blanca básica y una chaqueta oversize. Para los zapatos, unos tenis blancos o mocasines dependiendo de la ocasión.",
  },
  {
    id: 3,
    pregunta: "¿Qué colores están de moda esta temporada?",
    respuesta:
      "Esta temporada mandan los tonos tierra, el verde oliva, el rosa pastel y el azul eléctrico. También los neutros como beige y crema son infalibles para cualquier outfit.",
  },
  {
    id: 4,
    pregunta: "Recomiéndame un outfit casual",
    respuesta:
      "Un outfit casual ideal: jeans rectos de tiro medio, una polera oversize de algodón, zapatillas blancas y una mochila de cuero. Sencillo pero con estilo.",
  },
];

function ChatFlotante() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "¡Hola! Soy tu Asesor de Imagen IA. Pregúntame sobre moda, combinaciones o tendencias.",
    },
  ]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);

  const handleQuestionClick = (item) => {
    setSelectedQuestion(item.id);
    setMessages((prev) => [
      ...prev,
      { role: "user", text: item.pregunta },
      { role: "assistant", text: item.respuesta },
    ]);
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-r from-fashion-pink to-fashion-purple text-white shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 flex items-center justify-center"
      >
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
      </button>

      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-bounce-in origin-bottom-right">
          <div className="bg-gradient-to-r from-fashion-pink to-fashion-purple p-4 text-white">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 className="font-serif font-semibold text-sm">Asesor de Imagen</h3>
                <p className="text-xs text-white/70">IA de moda • Online</p>
              </div>
            </div>
          </div>

          <div className="h-80 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                    msg.role === "user"
                      ? "bg-gradient-to-r from-fashion-pink to-fashion-purple text-white rounded-br-md"
                      : "bg-gray-100 text-gray-700 rounded-bl-md"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-gray-100 p-3">
            <p className="text-[11px] text-gray-400 font-medium uppercase tracking-wider mb-2">
              Preguntas rápidas:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {respuestasMock.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleQuestionClick(item)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                    selectedQuestion === item.id
                      ? "bg-fashion-pink text-white border-fashion-pink"
                      : "bg-white text-gray-500 border-gray-200 hover:border-fashion-pink hover:text-fashion-pink"
                  }`}
                >
                  {item.pregunta}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default ChatFlotante;
