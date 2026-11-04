import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X, Sparkles, User, Crown, Camera, Send } from "lucide-react";
import { useSelector, useDispatch } from "react-redux";
import api from "../services/api";
import { useFeatureGate } from "../hooks/useFeatureGate";
import { setDailyUsage } from "../store/userSlice";
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
    isUnlimited,
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

  const dispatch = useDispatch();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: isPremium
        ? "Bienvenido de vuelta. Tu asesor IA premium esta listo. Que necesitas hoy?"
        : `Hola! Soy Liney, tu Asesor de Imagen IA. Tienes ${isUnlimited ? "mensajes ilimitados" : `${llmRemaining} mensajes gratis`} hoy. Preguntame sobre moda, combinaciones o tendencias.`,
      products: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);

  const handleToggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const sendMessage = async (text, imgBase64 = null) => {
    if (!text.trim() && !imgBase64) return;
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

    const userMsg = { role: "user", text: text.trim(), products: [], image: imgBase64 };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setImagePreview(null);
    setLoading(true);

    try {
      const res = await api.post("/recommendations/chat", {
        question: text.trim() || "Analiza esta imagen.",
        image: imgBase64 || undefined,
      });
      const advice = res.data?.advice || "No pude generar un consejo.";
      const products = res.data?.products || [];
      if (res.data?.daily_usage) {
        dispatch(setDailyUsage(res.data.daily_usage));
      }
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
    sendMessage(input, imagePreview);
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
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed ${
                          msg.role === "user"
                            ? "bg-editorial-black text-white rounded-br-md"
                            : "bg-editorial-cream text-editorial-charcoal rounded-bl-md"
                        }`}
                      >
                        {msg.image && (
                           <div className="mb-2">
                             <img src={msg.image} alt="User Upload" className="max-w-full h-auto rounded-lg" />
                           </div>
                        )}
                        {msg.role === "assistant" ? renderAdvice(msg.text) : msg.text}
                      </div>
                    </div>
                    {msg.products && msg.products.length > 0 && (
                      <div className="flex gap-2 pl-2 overflow-x-auto">
                        {msg.products.map((product) => (
                          <ProductMiniCard key={product.id} product={product} />
                        ))}
                      </div>
                    )}
                    {msg.role === "assistant" && i === 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {quickQuestions.map((q, j) => (
                          <button
                            key={j}
                            onClick={() => sendMessage(q)}
                            disabled={!canUseLlm || loading}
                            className="text-[11px] px-3 py-1.5 rounded-full border border-editorial-black/10 text-editorial-gray hover:border-editorial-black hover:text-editorial-black transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                          >
                            {q}
                          </button>
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

              {/* Input Area */}
              <div className="border-t border-editorial-black/5 p-3">
                {canUseLlm ? (
                  <form onSubmit={handleSubmit} className="flex flex-col gap-2">
                    {imagePreview && (
                      <div className="relative w-16 h-16 rounded-lg overflow-hidden border border-editorial-black/10">
                        <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                        <button
                          type="button"
                          onClick={() => setImagePreview(null)}
                          className="absolute top-1 right-1 w-4 h-4 bg-black/50 rounded-full flex items-center justify-center"
                        >
                          <X size={10} className="text-white" />
                        </button>
                      </div>
                    )}
                    <div className="flex items-center gap-2 bg-editorial-cream rounded-full px-3 py-1.5">
                      <label className="cursor-pointer shrink-0 p-1.5 hover:bg-editorial-black/5 rounded-full transition-colors">
                        <Camera size={16} className="text-editorial-gray hover:text-editorial-black" />
                        <input type="file" accept="image/*" className="hidden" onChange={handleImageUpload} disabled={loading} />
                      </label>
                      <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Escribe tu pregunta..."
                        className="flex-1 text-[13px] bg-transparent focus:outline-none placeholder-editorial-gray/60"
                        disabled={loading}
                      />
                      {(input.trim() || imagePreview) && (
                        <button
                          type="submit"
                          disabled={loading}
                          className="shrink-0 p-1.5 bg-editorial-black text-white rounded-full hover:bg-editorial-black/80 transition-colors disabled:opacity-50"
                        >
                          <Send size={14} />
                        </button>
                      )}
                    </div>
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
