const tiendas = [
  { nombre: "Paris", clase: "bg-editorial-blue-light text-white hover:bg-editorial-blue-dark transition-colors" },
  { nombre: "Maui", clase: "bg-teal-500 text-white hover:bg-teal-600 transition-colors" },
  { nombre: "Zara", clase: "bg-black text-white hover:bg-gray-800 transition-colors" },
  { nombre: "Falabella", clase: "bg-green-600 text-white hover:bg-green-700 transition-colors" },
  { nombre: "H&M", clase: "bg-red-600 text-white hover:bg-red-700 transition-colors" },
  { nombre: "Hites", clase: "bg-blue-600 text-white hover:bg-blue-700 transition-colors" },
  { nombre: "Fashion Park", clase: "bg-pink-500 text-white hover:bg-pink-600 transition-colors" },
  { nombre: "H&M", clase: "bg-red-600 text-white hover:bg-red-700 transition-colors" }
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
