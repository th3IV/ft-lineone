const tiendas = [
  { nombre: "Paris", clase: "bg-editorial-black" },
  { nombre: "Maui", clase: "bg-teal-500" },
  { nombre: "Zara", clase: "bg-black" },
];

function FiltroTiendas({ selected, onChange }) {
  return (
    <div>
      <h4 className="editorial-label mb-3">Tiendas</h4>
      <div className="flex flex-wrap gap-2">
        {tiendas.map((t) => (
          <button
            key={t.nombre}
            onClick={() =>
              onChange(
                selected === t.nombre.toLowerCase() ? null : t.nombre.toLowerCase()
              )
            }
            className={`tag-pill flex items-center gap-1.5 ${
              selected === t.nombre.toLowerCase()
                ? "tag-pill-active"
                : "bg-editorial-white text-editorial-gray hover:border-editorial-black/20"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${t.clase} ${
                selected === t.nombre.toLowerCase()
                  ? "ring-1 ring-white/60"
                  : ""
              }`}
            />
            {t.nombre}
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroTiendas;
