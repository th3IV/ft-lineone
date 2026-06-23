function FiltroPrecio({ minPrice, maxPrice, onChange }) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
        Rango de Precio
      </h4>
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
          <input
            type="number"
            placeholder="Mín"
            value={minPrice || ""}
            onChange={(e) => onChange({ min: e.target.value || null, max: maxPrice })}
            className="w-full border border-gray-200 rounded-xl pl-7 pr-3 py-2 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent bg-white"
          />
        </div>
        <span className="text-gray-300">—</span>
        <div className="relative flex-1">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
          <input
            type="number"
            placeholder="Máx"
            value={maxPrice || ""}
            onChange={(e) => onChange({ min: minPrice, max: e.target.value || null })}
            className="w-full border border-gray-200 rounded-xl pl-7 pr-3 py-2 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent bg-white"
          />
        </div>
      </div>
    </div>
  );
}

export default FiltroPrecio;
