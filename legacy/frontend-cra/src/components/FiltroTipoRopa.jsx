const tipos = [
  "Poleras",
  "Camisas",
  "Pantalones",
  "Shorts",
  "Chaquetas",
  "Vestidos",
  "Faldas",
  "Polerones",
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
      <h4 className="editorial-label mb-3">Tipo de Ropa</h4>
      <div className="flex flex-wrap gap-1.5">
        {tipos.map((tipo) => (
          <button
            key={tipo}
            onClick={() => toggle(tipo)}
            className={`tag-pill text-[11px] ${
              selected.includes(tipo)
                ? "tag-pill-active"
                : "bg-editorial-white text-editorial-gray hover:border-editorial-black/20"
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
