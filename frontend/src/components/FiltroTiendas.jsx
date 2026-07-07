const tiendas = [
  { nombre: "Maui", slug: "maui", clase: "bg-teal-500 text-white hover:bg-teal-600 transition-colors" },
  { nombre: "Zara", slug: "zara", clase: "bg-black text-white hover:bg-gray-800 transition-colors" },
  { nombre: "Falabella", slug: "falabella", clase: "bg-green-600 text-white hover:bg-green-700 transition-colors" },
  { nombre: "H&M", slug: "hm", clase: "bg-red-600 text-white hover:bg-red-700 transition-colors" },
  { nombre: "Fashion Park", slug: "fashionpark", clase: "bg-pink-500 text-white hover:bg-pink-600 transition-colors" }
];

function FiltroTiendas({ selected, onChange }) {
  return (
    <div>
      <h4 className="editorial-label mb-3">Tiendas</h4>
      <div className="flex flex-wrap gap-2">
        {tiendas.map((t) => (
          <button
            key={t.slug}
            onClick={() =>
              onChange(
                selected === t.slug ? null : t.slug
              )
            }
            className={`tag-pill flex items-center gap-1.5 ${
              selected === t.slug
                ? "tag-pill-active"
                : "bg-editorial-white text-editorial-gray hover:border-editorial-black/20"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${t.clase} ${
                selected === t.slug
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
