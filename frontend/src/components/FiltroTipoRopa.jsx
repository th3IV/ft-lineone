const tipos = [
  "Poleras",
  "Camisas",
  "Pantalones",
  "Shorts",
  "Chaquetas",
  "Vestidos",
  "Faldas",
  "Polerones",
  "Accesorios",
  "Calzado",
];

function FiltroTipoRopa({ selected, onChange }) {
  const toggle = (tipo) => {
    if (selected.includes(tipo)) {
      onChange(selected.filter((t) => t !== tipo));
    } else {
      onChange([...selected, tipo]);
    }
  };

  return (
    <div>
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
        Tipo de Ropa
      </h4>
      <div className="flex flex-wrap gap-1.5">
        {tipos.map((tipo) => (
          <button
            key={tipo}
            onClick={() => toggle(tipo)}
            className={`tag-pill text-xs ${
              selected.includes(tipo)
                ? "bg-fashion-purple text-white border-fashion-purple"
                : "bg-white text-gray-600 border-gray-200 hover:border-fashion-purple"
            }`}
          >
            {tipo}
          </button>
        ))}
      </div>
    </div>
  );
}

export default FiltroTipoRopa;
