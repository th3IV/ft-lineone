import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X, Sparkles, User, Crown } from "lucide-react";
import { useSelector } from "react-redux";
import api from "../services/api";
import { useFeatureGate } from "../hooks/useFeatureGate";
import UpgradeModal from "./UpgradeModal";

const quickQuestions = [
  "Que me recomiendas para una fiesta?",
  "Como combino este pantalon?",
  "Que colores estan de moda?",
  "Recomiendame un outfit casual",
];

function renderAdvice(text) {
  if (!text) return null;
  const parts = text.split(/(\[[^\]]+\]\([^)]+\))/g);
  return parts.map((part, i) => {
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (linkMatch) {
      let label = linkMatch[1];
      const to = linkMatch[2];
      label = label.replace(/^\*\*(.+)\*\*$/, "$1");
      return (
        <Link
          key={i}
          to={to}
          className="font-semibold underline underline-offset-2 hover:text-editorial-black transition-colors"
        >
          {label}
        </Link>
      );
    }
    const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
    return boldParts.map((bp, j) => {
      if (bp.startsWith("**") && bp.endsWith("**")) {
        return <strong key={`${i}-${j}`}>{bp.slice(2, -2)}</strong>;
      }
      return bp;
    });
  });
}

function ProductMiniCard({ product }) {
  const image = product.image_urls?.[0] || product.image_url;
  if (!image) return null;
  return (
    <Link
      to={`/product/${product.id}`}
      className="block w-16 h-16 rounded-lg overflow-hidden border border-editorial-black/5 hover:border-editorial-black/20 transition-colors flex-shrink-0"
    >
      <img src={image} alt={product.name} className="w-full h-full object-cover" />
    </Link>
  );
}

function Avatar({ src, fallback, className }) {
  return (
    <div className={`rounded-full overflow-hidden bg-editorial-gray-light/30 flex items-center justify-center ${className}`}>
      {src ? (
        <img src={src} alt="Avatar" className="w-full h-full object-cover" />
      ) : (
        <User size={16} className="text-editorial-gray" />
      )}
    </div>
  );
}

function ChatFlotante() {
  const { user } = useSelector((state) => state.user);
  const {
    isPremium,
    llmUsed,
    llmRemaining,
    canUseLlm,
    getUsageColor,
    showUpgrade,
    showUpgradeModal,
    hideUpgradeModal,
    handleUpgrade,
    upgradeLoading,
    upgradeError,
    limits,
  } = useFeatureGate();

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: isPremium
        ? "Hola! Soy Liney, tu Asesor de Imagen IA personal. Preguntame sobre moda, combinaciones o tendencias. Estoy aqui para ayudarte a encontrar el look perfecto."
        : `Hola! Soy Liney, tu Asesor de Imagen IA. Tienes ${limits.llm - llmUsed} mensajes gratis hoy. Preguntame sobre moda, combinaciones o tendencias.`,
      products: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleToggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  const sendMessage = async (text) => {
    if (!text.trim()) return;
    if (!canUseLlm) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Se acabaron tus mensajes de hoy. Opta por la version Premium para un chat ilimitado.",
          products: [],
        },
      ]);
      return;
    }

    const userMsg = { role: "user", text: text.trim(), products: [] };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/recommendations/chat", {
        question: text.trim(),
      });
      const advice = res.data?.advice || "No pude generar un consejo.";
      const products = res.data?.products || [];
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: advice, products },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Servicio no disponible temporalmente.", products: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <>
      {/* Toggle Button */}
      <motion.button
        onClick={handleToggleChat}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full overflow-hidden shadow-[0_8px_30px_rgba(0,0,0,0.2)] hover:shadow-[0_12px_40px_rgba(0,0,0,0.3)] transition-shadow duration-300 flex items-center justify-center"
      >
        <img
          src="/logo.jpg"
          alt="FT. THE LINE ONE"
          className="w-14 h-14 rounded-full object-cover"
        />
        <AnimatePresence mode="wait">
          {isOpen && (
            <motion.div
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0 bg-editorial-black flex items-center justify-center"
            >
              <X size={20} className="text-white" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="fixed bottom-24 right-6 z-50 w-80 sm:w-96 bg-editorial-white rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.15)] border border-editorial-black/5 overflow-hidden"
            >
              {/* Header */}
              <div className="bg-editorial-black p-4 text-white">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center">
                    <Sparkles size={16} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-display font-semibold text-sm">
                      Asesor de Imagen
                    </h3>
                    <p className="text-[11px] text-white/50">IA de moda</p>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="h-80 overflow-y-auto p-4 space-y-3">
                {messages.map((msg, i) => (
                  <div key={i} className="space-y-2">
                    <div
                      className={`flex items-end gap-2 ${
                        msg.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      {msg.role === "assistant" && (
                        <div className="w-6 h-6 rounded-full bg-editorial-black/5 flex items-center justify-center shrink-0">
                          <Sparkles size={12} className="text-editorial-black" />
                        </div>
                      )}
                      <div
                        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed ${
                          msg.role === "user"
                            ? "bg-editorial-black text-white rounded-br-md"
                            : "bg-editorial-cream text-editorial-charcoal rounded-bl-md"
                        }`}
                      >
                        {msg.role === "assistant" ? renderAdvice(msg.text) : msg.text}
                      </div>
                      {msg.role === "user" && (
                        <Avatar
                          src={user?.profile_image}
                          fallback={<User size={12} />}
                          className="w-6 h-6 shrink-0"
                        />
                      )}
                    </div>
                    {msg.products && msg.products.length > 0 && (
                      <div className="flex gap-2 pl-2 overflow-x-auto">
                        {msg.products.map((product) => (
                          <ProductMiniCard key={product.id} product={product} />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-editorial-cream rounded-2xl rounded-bl-md px-4 py-3">
                      <div className="flex gap-1">
                        <span className="w-1.5 h-1.5 bg-editorial-gray-light rounded-full animate-pulse-soft" />
                        <span className="w-1.5 h-1.5 bg-editorial-gray-light rounded-full animate-pulse-soft [animation-delay:0.2s]" />
                        <span className="w-1.5 h-1.5 bg-editorial-gray-light rounded-full animate-pulse-soft [animation-delay:0.4s]" />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Questions + Input */}
              <div className="border-t border-editorial-black/5 p-3">
                {messages.filter(m => m.role === "user").length === 0 && (
                  <>
                    <p className="editorial-label text-[10px] mb-2">
                      Preguntas rapidas
                    </p>
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {quickQuestions.map((q, i) => (
                        <button
                          key={i}
                          onClick={() => sendMessage(q)}
                          disabled={!canUseLlm}
                          className="text-[11px] px-3 py-1.5 rounded-full border border-editorial-black/10 text-editorial-gray hover:border-editorial-black hover:text-editorial-black transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </>
                )}
                {canUseLlm ? (
                  <form onSubmit={handleSubmit} className="flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Escribe tu pregunta..."
                      className="flex-1 text-[13px] border-b border-editorial-black/10 rounded-none px-0 py-2 bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
                      disabled={loading}
                    />
                    <button
                      type="submit"
                      disabled={loading || !input.trim()}
                      className="text-[12px] font-medium text-editorial-black disabled:opacity-30 transition-colors"
                    >
                      Enviar
                    </button>
                  </form>
                ) : (
                  <button
                    onClick={showUpgradeModal}
                    className="w-full py-2.5 bg-editorial-black text-white rounded-xl text-xs font-medium flex items-center justify-center gap-2"
                  >
                    <Crown size={12} />
                    Upgrade para seguir chateando
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      <UpgradeModal
        isOpen={showUpgrade}
        onClose={hideUpgradeModal}
        onUpgrade={handleUpgrade}
        loading={upgradeLoading}
        error={upgradeError}
      />
    </>
  );
}

export default ChatFlotante;
