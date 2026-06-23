const generos = ["Hombre", "Mujer", "Unisex", "Niños"];

const iconos = {
  Hombre: "M",
  Mujer: "F",
  Unisex: "U",
  Niños: "K",
};

function FiltroGenero({ selected, onChange }) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
        Género
      </h4>
      <div className="flex flex-wrap gap-2">
        {generos.map((g) => (
          <button
            key={g}
            onClick={() => onChange(selected === g ? null : g)}
            className={`tag-pill ${
              selected === g
                ? "bg-fashion-pink text-white border-fashion-pink"
                : "bg-white text-gray-600 border-gray-200 hover:border-fashion-pink"
            }`}
          >
            {iconos[g]}
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroGenero;
