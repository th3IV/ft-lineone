const tallas = ["XS", "S", "M", "L", "XL", "XXL"];

function FiltroTallas({ selected, onChange }) {
  return (
    <div>
      <h4 className="editorial-label mb-3">Talla</h4>
      <div className="flex flex-wrap gap-1.5">
        {tallas.map((t) => (
          <button
            key={t}
            onClick={() => onChange(selected === t ? null : t)}
            className={`tag-pill min-w-[2.5rem] text-center ${
              selected === t
                ? "tag-pill-active"
                : "bg-editorial-white text-editorial-gray hover:border-editorial-black/20"
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
