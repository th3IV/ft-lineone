import { motion } from "framer-motion";
import { Crown, Sparkles, X } from "lucide-react";
import { useState } from "react";

export default function PremiumBanner({ onUpgrade }) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <motion.button
      onClick={onUpgrade}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="group relative w-full text-left overflow-hidden cursor-pointer"
      style={{
        background:
          "linear-gradient(90deg, #0a0a0a 0%, #1a1a2e 25%, #7c3aed 50%, #ec4899 75%, #0a0a0a 100%)",
        backgroundSize: "400% 100%",
      }}
    >
      {/* Shimmer overlay — se acelera en hover */}
      <div
        className="absolute inset-0 pointer-events-none transition-all duration-500"
        style={{
          background:
            "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.08) 50%, transparent 100%)",
          backgroundSize: "200% 100%",
          animation: "shimmer 3s ease-in-out infinite",
        }}
      />

      {/* Brillo extra en hover */}
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-500 pointer-events-none" />

      <div className="relative max-w-[1400px] mx-auto px-5 sm:px-8 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {/* Crown con glow pulsante — rota y crece en hover */}
          <div className="relative w-9 h-9 rounded-full bg-white/10 flex items-center justify-center shrink-0 animate-pulse-glow group-hover:bg-white/20 transition-all duration-500">
            <Crown
              size={16}
              className="text-editorial-gold relative z-10 transition-all duration-500 group-hover:scale-125 group-hover:rotate-12"
            />
          </div>

          <p className="text-xs sm:text-sm text-white truncate transition-all duration-300">
            <span className="font-semibold">Premium</span> — Pruebas
            ilimitadas, chat IA y mas.
            <span className="ml-2 inline-flex items-center gap-1 text-editorial-gold font-semibold group-hover:text-white transition-colors duration-300">
              Upgrade $4.990/mes
              <Sparkles
                size={12}
                className="animate-sparkle-twinkle group-hover:scale-125 transition-transform duration-300"
              />
            </span>
          </p>
        </div>

        {/* Particulas flotantes — mas visibles en hover */}
        <Sparkles
          size={14}
          className="absolute top-1 right-16 text-white/30 animate-float-particle group-hover:text-white/60 transition-colors duration-500"
          style={{ animationDelay: "0s" }}
        />
        <Sparkles
          size={10}
          className="absolute bottom-1 right-24 text-white/20 animate-float-particle group-hover:text-white/50 transition-colors duration-500"
          style={{ animationDelay: "2s" }}
        />
        <Sparkles
          size={12}
          className="absolute top-1 left-1/3 text-white/25 animate-float-particle group-hover:text-white/55 transition-colors duration-500"
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
