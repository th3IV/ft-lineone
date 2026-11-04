import { motion, AnimatePresence } from "framer-motion";
import { createPortal } from "react-dom";

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpgrade: () => void;
  loading?: boolean;
  error?: string | null;
}

export const UpgradeModal = ({
  isOpen,
  onClose,
  onUpgrade,
  loading = false,
  error = null,
}: UpgradeModalProps) => {
  if (!isOpen) return null;

  return createPortal(
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-editorial-black/70 backdrop-blur-sm"
          onClick={onClose}
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="relative bg-editorial-white rounded-2xl shadow-2xl w-full max-w-md p-8"
        >
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 text-editorial-gray hover:text-editorial-black rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full bg-editorial-gold/10 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-editorial-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2m0 0v5.586a1 1 0 01-.293.707l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" />
              </svg>
            </div>
            <h2 className="font-display text-2xl font-semibold text-editorial-black mb-2">
              Desbloquea Premium
            </h2>
            <p className="text-editorial-gray text-sm">
              Pruebas virtuales ilimitadas, recomendaciones avanzadas y mas beneficios exclusivos.
            </p>
          </div>

          <div className="space-y-3 mb-6">
            <div className="flex items-center gap-3 text-sm">
              <svg className="w-5 h-5 text-editorial-gold flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-editorial-black">Pruebas virtuales ilimitadas</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <svg className="w-5 h-5 text-editorial-gold flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-editorial-black">Recomendaciones con IA personalizadas</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <svg className="w-5 h-5 text-editorial-gold flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-editorial-black">Soporte prioritario</span>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={onUpgrade}
            disabled={loading}
            className="w-full btn-primary py-3"
          >
            {loading ? "Procesando..." : "Hacerme Premium"}
          </button>

          <button
            onClick={onClose}
            className="w-full mt-2 text-sm text-editorial-gray hover:text-editorial-black py-2 transition-colors"
          >
            Ahora no
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>,
    document.body
  );
};
