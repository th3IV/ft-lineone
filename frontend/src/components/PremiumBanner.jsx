import { Crown, Zap, ArrowRight, X } from "lucide-react";
import { useState } from "react";

export default function PremiumBanner({ onUpgrade }) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="relative bg-editorial-black text-white overflow-hidden">
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shrink-0">
            <Crown size={14} className="text-editorial-gold" />
          </div>
          <p className="text-xs sm:text-sm truncate">
            <span className="font-semibold">Premium</span> — Pruebas ilimitadas, chat IA y mas.
            <button
              onClick={onUpgrade}
              className="ml-2 inline-flex items-center gap-1 text-editorial-gold hover:text-white font-medium transition-colors"
            >
              Upgrade $4.990/mes
              <ArrowRight size={12} />
            </button>
          </p>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="p-1 text-white/30 hover:text-white transition-colors shrink-0"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}
