const colores = [
  { nombre: "Negro", clase: "bg-black" },
  { nombre: "Blanco", clase: "bg-white border border-editorial-black/10" },
  { nombre: "Rojo", clase: "bg-red-500" },
  { nombre: "Azul", clase: "bg-blue-500" },
  { nombre: "Verde", clase: "bg-green-500" },
  { nombre: "Rosa", clase: "bg-pink-400" },
  { nombre: "Amarillo", clase: "bg-yellow-400" },
  { nombre: "Gris", clase: "bg-gray-400" },
  { nombre: "Beige", clase: "bg-amber-100 border border-amber-200" },
  { nombre: "Morado", clase: "bg-purple-500" },
];

function FiltroColores({ selected, onChange }) {
  return (
    <div>
      <h4 className="editorial-label mb-3">Color</h4>
      <div className="flex flex-wrap gap-2.5">
        {colores.map((c) => (
          <button
            key={c.nombre}
            onClick={() => onChange(selected === c.nombre ? null : c.nombre)}
            className="flex flex-col items-center gap-1 group"
            title={c.nombre}
          >
            <span
              className={`w-7 h-7 rounded-full ${c.clase} ring-offset-2 transition-all duration-200 ${
                selected === c.nombre
                  ? "ring-2 ring-editorial-black scale-110"
                  : "ring-0 hover:ring-1 hover:ring-editorial-black/20"
              }`}
            />
            <span className="text-[9px] text-editorial-gray group-hover:text-editorial-black transition-colors">
              {c.nombre}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroColores;
