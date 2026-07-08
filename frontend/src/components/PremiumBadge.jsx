import { Sparkles } from "lucide-react";

function PremiumBadge({ size = "sm", className = "" }) {
  const sizes = {
    xs: "px-1.5 py-0.5 text-[9px] gap-0.5",
    sm: "px-2 py-0.5 text-[10px] gap-1",
    md: "px-3 py-1 text-xs gap-1.5",
  };

  const iconSizes = { xs: 8, sm: 10, md: 12 };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full bg-gradient-to-r from-amber-100 to-orange-100 text-amber-700 border border-amber-200/50 ${sizes[size]} ${className}`}
    >
      <Sparkles size={iconSizes[size]} className="text-amber-500" />
      Premium
    </span>
  );
}

export default PremiumBadge;
