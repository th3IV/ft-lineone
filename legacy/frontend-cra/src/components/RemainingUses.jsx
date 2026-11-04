import { Crown } from "lucide-react";

const COLOR_MAP = {
  green: { bar: "bg-emerald-500", text: "text-emerald-600" },
  yellow: { bar: "bg-yellow-400", text: "text-yellow-600" },
  orange: { bar: "bg-orange-400", text: "text-orange-600" },
  red: { bar: "bg-red-500", text: "text-red-600" },
};

function RemainingUses({ type, used, limit, color }) {
  const remaining = Math.max(0, limit - used);
  const pct = Math.min((used / limit) * 100, 100);
  const colors = COLOR_MAP[color] || COLOR_MAP.green;
  const label = type === "vton" ? "Pruebas de vestir" : "Mensajes IA";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-editorial-gray">{label}</span>
        <div className="flex items-center gap-1.5">
          <span className={`text-xs font-semibold ${colors.text}`}>
            {remaining}
          </span>
          <span className="text-[10px] text-editorial-gray-light">
            de {limit} restantes
          </span>
        </div>
      </div>
      <div className="h-1.5 bg-editorial-gray-light/30 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colors.bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {remaining <= 3 && remaining > 0 && (
        <p className="text-[10px] text-editorial-gray flex items-center gap-1">
          <Crown size={10} className="text-amber-500" />
          Upgrade a premium para uso ilimitado
        </p>
      )}
      {remaining === 0 && (
        <p className="text-[10px] text-red-500 font-medium flex items-center gap-1">
          <Crown size={10} />
          Limite diario alcanzado
        </p>
      )}
    </div>
  );
}

export default RemainingUses;
