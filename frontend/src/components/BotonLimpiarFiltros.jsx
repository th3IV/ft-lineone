function BotonLimpiarFiltros({ onClick, hasFilters }) {
  if (!hasFilters) return null;

  return (
    <button
      onClick={onClick}
      className="w-full py-2.5 rounded-xl border-2 border-gray-200 text-sm font-medium text-gray-500 hover:text-fashion-pink hover:border-fashion-pink transition-all duration-200 active:scale-[0.98]"
    >
      Limpiar todos los filtros
    </button>
  );
}

export default BotonLimpiarFiltros;
