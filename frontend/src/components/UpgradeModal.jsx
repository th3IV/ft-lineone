import { motion, AnimatePresence } from "framer-motion";
import { X, Crown, Sparkles, Shirt, MessageCircle, Clock, Zap } from "lucide-react";

const BENEFITS = [
  { icon: Shirt, text: "Pruebas de vestir ilimitadas con IA" },
  { icon: Sparkles, text: "Recomendaciones personalizadas" },
  { icon: MessageCircle, text: "Chat con asesor de moda IA" },
  { icon: Clock, text: "Historial completo de looks" },
  { icon: Zap, text: "Sin interrupciones ni limites" },
];

function UpgradeModal({ isOpen, onClose, onUpgrade }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 20 }}
            transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="relative bg-white w-full max-w-md rounded-2xl overflow-hidden shadow-[0_25px_60px_rgba(0,0,0,0.2)]"
          >
            {/* Header */}
            <div className="relative bg-editorial-black px-6 pt-8 pb-10 text-center">
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 text-white/40 hover:text-white transition-colors"
              >
                <X size={18} />
              </button>
              <div className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center mx-auto mb-4">
                <Crown size={24} className="text-editorial-gold" />
              </div>
              <h2 className="font-display text-xl font-bold text-white tracking-tight">
                Desbloquea FT. THE LINE ONE Premium
              </h2>
              <p className="text-sm text-white/50 mt-1">
                La experiencia completa de moda con inteligencia artificial
              </p>
            </div>

            {/* Benefits */}
            <div className="px-6 -mt-5 relative z-10">
              <div className="bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.06)] border border-editorial-black/5 p-5">
                <div className="space-y-3">
                  {BENEFITS.map(({ icon: Icon, text }, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-editorial-cream flex items-center justify-center shrink-0">
                        <Icon size={14} className="text-editorial-black" />
                      </div>
                      <span className="text-sm text-editorial-charcoal">{text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* CTA */}
            <div className="px-6 pt-5 pb-6">
              <button
                onClick={onUpgrade}
                className="w-full py-3.5 bg-editorial-black text-white rounded-xl text-sm font-semibold hover:bg-editorial-black/90 transition-all flex items-center justify-center gap-2 shadow-[0_4px_15px_rgba(0,0,0,0.15)]"
              >
                <Zap size={15} />
                Upgrade por $4.990/mes
              </button>
              <div className="flex items-center justify-center gap-3 mt-3">
                <button
                  onClick={onClose}
                  className="text-xs text-editorial-gray hover:text-editorial-black transition-colors"
                >
                  Tal vez despues
                </button>
              </div>
              <p className="text-[10px] text-editorial-gray-light text-center mt-3">
                Cancela cuando quieras · Pago seguro con Transbank
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default UpgradeModal;
