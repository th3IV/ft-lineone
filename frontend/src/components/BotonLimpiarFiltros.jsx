function BotonLimpiarFiltros({ onClick, hasFilters }) {
  if (!hasFilters) return null;

  return (
    <button
      onClick={onClick}
      className="w-full py-2.5 rounded-full border border-editorial-black/10 text-xs font-medium text-editorial-gray hover:text-editorial-black hover:border-editorial-black/30 transition-all duration-200"
    >
      Limpiar todos los filtros
    </button>
  );
}

export default BotonLimpiarFiltros;
