function FiltroOrden({ selected, onChange }) {
  return (
    <div>
      <h4 className="editorial-label mb-3">Ordenar por</h4>
      <div className="flex flex-wrap gap-2">
        {[
          { value: null, label: "Relevancia" },
          { value: "price_asc", label: "Precio menor" },
          { value: "price_desc", label: "Precio mayor" },
        ].map((opt) => (
          <button
            key={opt.label}
            onClick={() => onChange(opt.value)}
            className={`tag-pill ${
              selected === opt.value
                ? "tag-pill-active"
                : "bg-editorial-white text-editorial-gray hover:border-editorial-black/20"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroOrden;
