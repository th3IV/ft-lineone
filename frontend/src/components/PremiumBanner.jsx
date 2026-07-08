import { motion } from "framer-motion";
import { Crown, Sparkles, X } from "lucide-react";
import { useState } from "react";

export default function PremiumBanner({ onUpgrade }) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <motion.button
      onClick={onUpgrade}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      transition={{ duration: 0.2 }}
      className="relative w-full text-left overflow-hidden cursor-pointer"
      style={{
        background:
          "linear-gradient(90deg, #0a0a0a 0%, #1a1a2e 25%, #7c3aed 50%, #ec4899 75%, #0a0a0a 100%)",
        backgroundSize: "400% 100%",
      }}
    >
      {/* Shimmer overlay */}
      <div className="absolute inset-0 animate-shimmer pointer-events-none" />

      <div className="relative max-w-[1400px] mx-auto px-5 sm:px-8 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {/* Crown con glow pulsante */}
          <div className="relative w-9 h-9 rounded-full bg-white/10 flex items-center justify-center shrink-0 animate-pulse-glow">
            <Crown size={16} className="text-editorial-gold relative z-10" />
          </div>

          <p className="text-xs sm:text-sm text-white truncate">
            <span className="font-semibold">Premium</span> — Pruebas
            ilimitadas, chat IA y mas.
            <span className="ml-2 inline-flex items-center gap-1 text-editorial-gold font-semibold">
              Upgrade $4.990/mes
              <Sparkles
                size={12}
                className="animate-sparkle-twinkle"
              />
            </span>
          </p>
        </div>

        {/* Particulas flotantes */}
        <Sparkles
          size={14}
          className="absolute top-1 right-16 text-white/30 animate-float-particle"
          style={{ animationDelay: "0s" }}
        />
        <Sparkles
          size={10}
          className="absolute bottom-1 right-24 text-white/20 animate-float-particle"
          style={{ animationDelay: "2s" }}
        />
        <Sparkles
          size={12}
          className="absolute top-1 left-1/3 text-white/25 animate-float-particle"
          style={{ animationDelay: "4s" }}
        />

        {/* Boton dismiss — stopPropagation para no activar upgrade */}
        <span
          role="button"
          tabIndex={0}
          onClick={(e) => {
            e.stopPropagation();
            setDismissed(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.stopPropagation();
              setDismissed(true);
            }
          }}
          className="relative p-1 text-white/30 hover:text-white transition-colors shrink-0 cursor-pointer z-10"
        >
          <X size={14} />
        </span>
      </div>
    </motion.button>
  );
}
