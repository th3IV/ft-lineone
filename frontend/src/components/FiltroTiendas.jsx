const tiendas = [
  { nombre: "Falabella", clase: "bg-green-600" },
  { nombre: "Ripley", clase: "bg-red-600" },
  { nombre: "Paris", clase: "bg-blue-600" },
  { nombre: "Maui", clase: "bg-teal-500" },
  { nombre: "Zara", clase: "bg-black" },
];

function FiltroTiendas({ selected, onChange }) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
        Tiendas
      </h4>
      <div className="flex flex-wrap gap-2">
        {tiendas.map((t) => (
          <button
            key={t.nombre}
            onClick={() => onChange(selected === t.nombre.toLowerCase() ? null : t.nombre.toLowerCase())}
            className={`tag-pill flex items-center gap-1.5 ${
              selected === t.nombre.toLowerCase()
                ? `${t.clase} text-white ring-2 ring-offset-1 ring-fashion-pink`
                : "bg-white text-gray-600 border-gray-200 hover:border-fashion-pink"
            }`}
          >
            <span className={`w-2.5 h-2.5 rounded-full ${t.clase} ${selected === t.nombre.toLowerCase() ? "ring-1 ring-white/60" : ""}`} />
            {t.nombre}
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroTiendas;
