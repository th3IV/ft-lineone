const generos = ["hombre", "mujer"];

function FiltroGenero({ selected, onChange }) {
  return (
    <div>
      <h4 className="editorial-label mb-3">Genero</h4>
      <div className="flex flex-wrap gap-2">
        {generos.map((g) => (
          <button
            key={g}
            onClick={() => onChange(selected === g ? null : g)}
            className={`tag-pill capitalize ${
              selected === g
                ? "tag-pill-active"
                : "bg-editorial-white text-editorial-gray hover:border-editorial-black/20"
            }`}
          >
            {g}
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroGenero;
