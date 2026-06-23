const tallas = ["XS", "S", "M", "L", "XL", "XXL"];

function FiltroTallas({ selected, onChange }) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
        Talla
      </h4>
      <div className="flex flex-wrap gap-1.5">
        {tallas.map((t) => (
          <button
            key={t}
            onClick={() => onChange(selected === t ? null : t)}
            className={`tag-pill min-w-[2.5rem] text-center ${
              selected === t
                ? "bg-editorial-charcoal text-white border-editorial-charcoal"
                : "bg-white text-gray-600 border-gray-200 hover:border-editorial-charcoal"
            }`}
          >
            {t}
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroTallas;
