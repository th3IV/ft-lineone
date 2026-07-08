import { motion, AnimatePresence } from "framer-motion";
import { X, Film, Sparkles } from "lucide-react";
import { useRewardedAd } from "../hooks/useRewardedAd";

export default function RewardedAd({ onComplete, onCancel }) {
  const { adCompleted, adLoading, showAd } = useRewardedAd();

  const handleWatch = async () => {
    await showAd();
    onComplete();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onCancel}
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 20 }}
          transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="relative bg-white w-full max-w-sm rounded-2xl overflow-hidden shadow-[0_25px_60px_rgba(0,0,0,0.2)]"
        >
          <button
            onClick={onCancel}
            className="absolute top-4 right-4 p-2 text-editorial-gray/40 hover:text-editorial-black transition-colors z-10"
          >
            <X size={18} />
          </button>

          <div className="p-8 text-center">
            <div className="w-14 h-14 rounded-full bg-editorial-cream flex items-center justify-center mx-auto mb-4">
              <Film size={22} className="text-editorial-black" />
            </div>
            <h3 className="font-display text-lg font-bold text-editorial-black mb-2">
              Mira un anuncio para continuar
            </h3>
            <p className="text-sm text-editorial-gray mb-6">
              Desbloquea esta prueba gratuita watching un anuncio corto.
            </p>

            {adLoading ? (
              <div className="flex items-center justify-center gap-2 py-3">
                <span className="w-4 h-4 rounded-full border-2 border-editorial-black/20 border-t-editorial-black animate-spin" />
                <span className="text-sm text-editorial-gray">Cargando anuncio...</span>
              </div>
            ) : (
              <button
                onClick={handleWatch}
                className="w-full py-3.5 bg-editorial-black text-white rounded-xl text-sm font-semibold hover:bg-editorial-black/90 transition-all flex items-center justify-center gap-2"
              >
                <Sparkles size={15} />
                Ver anuncio
              </button>
            )}

            <p className="text-[10px] text-editorial-gray-light mt-3">
              Tu prueba se desbloquea al completar el anuncio
            </p>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
