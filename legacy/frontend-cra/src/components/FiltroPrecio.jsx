function FiltroPrecio({ minPrice, maxPrice, onChange }) {
  return (
    <div>
      <h4 className="editorial-label mb-3">Rango de Precio</h4>
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <span className="absolute left-0 top-1/2 -translate-y-1/2 text-editorial-gray-light text-xs">
            $
          </span>
          <input
            type="number"
            placeholder="Min"
            value={minPrice || ""}
            onChange={(e) =>
              onChange({ min: e.target.value || null, max: maxPrice })
            }
            className="w-full border-b border-editorial-black/10 rounded-none pl-5 pr-2 py-2 text-xs bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
          />
        </div>
        <span className="text-editorial-gray-light text-xs">&mdash;</span>
        <div className="relative flex-1">
          <span className="absolute left-0 top-1/2 -translate-y-1/2 text-editorial-gray-light text-xs">
            $
          </span>
          <input
            type="number"
            placeholder="Max"
            value={maxPrice || ""}
            onChange={(e) =>
              onChange({ min: minPrice, max: e.target.value || null })
            }
            className="w-full border-b border-editorial-black/10 rounded-none pl-5 pr-2 py-2 text-xs bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
          />
        </div>
      </div>
    </div>
  );
}

export default FiltroPrecio;
