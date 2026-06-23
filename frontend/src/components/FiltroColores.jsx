const colores = [
  { nombre: "Negro", clase: "bg-black" },
  { nombre: "Blanco", clase: "bg-white border border-gray-300" },
  { nombre: "Rojo", clase: "bg-red-600" },
  { nombre: "Azul", clase: "bg-blue-600" },
  { nombre: "Verde", clase: "bg-green-600" },
  { nombre: "Rosa", clase: "bg-pink-400" },
  { nombre: "Amarillo", clase: "bg-yellow-400" },
  { nombre: "Gris", clase: "bg-gray-400" },
  { nombre: "Beige", clase: "bg-amber-100 border border-amber-200" },
  { nombre: "Morado", clase: "bg-purple-600" },
];

function FiltroColores({ selected, onChange }) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
        Color
      </h4>
      <div className="flex flex-wrap gap-2">
        {colores.map((c) => (
          <button
            key={c.nombre}
            onClick={() => onChange(selected === c.nombre ? null : c.nombre)}
            className="flex flex-col items-center gap-1 group"
            title={c.nombre}
          >
            <span
              className={`w-7 h-7 rounded-full ${c.clase} ring-offset-2 transition-all ${
                selected === c.nombre
                  ? "ring-2 ring-fashion-pink scale-110"
                  : "ring-0 hover:ring-1 hover:ring-gray-300"
              }`}
            />
            <span className="text-[10px] text-gray-500 group-hover:text-gray-700">
              {c.nombre}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroColores;
