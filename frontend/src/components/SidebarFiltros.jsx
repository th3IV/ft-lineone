import FiltroGenero from "./FiltroGenero";
import FiltroTiendas from "./FiltroTiendas";
import FiltroTipoRopa from "./FiltroTipoRopa";
import FiltroTallas from "./FiltroTallas";
import FiltroColores from "./FiltroColores";
import FiltroPrecio from "./FiltroPrecio";
import BotonLimpiarFiltros from "./BotonLimpiarFiltros";

function SidebarFiltros({
  isOpen,
  filters,
  onFilterChange,
  onClearFilters,
}) {
  const hasFilters =
    filters.gender ||
    filters.clothingType?.length > 0 ||
    filters.size ||
    filters.color ||
    filters.minPrice ||
    filters.maxPrice ||
    filters.store ||
    filters.query;

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-30 lg:hidden"
          onClick={() => onFilterChange("_toggle", null)}
        />
      )}

      <aside
        className={`fixed lg:sticky top-16 lg:top-24 left-0 z-40 lg:z-0 h-[calc(100vh-4rem)] lg:h-auto w-72 bg-white lg:bg-transparent border-r border-gray-100 lg:border-none overflow-y-auto transform transition-transform duration-300 lg:transform-none ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        } ${isOpen ? "shadow-2xl lg:shadow-none" : ""}`}
      >
        <div className="p-5 space-y-6">
          <div className="flex items-center justify-between lg:hidden">
            <h3 className="font-serif text-lg font-semibold">Filtros</h3>
            <button
              onClick={() => onFilterChange("_toggle", null)}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <FiltroGenero
            selected={filters.gender}
            onChange={(val) => onFilterChange("gender", val)}
          />

          <hr className="border-gray-100" />

          <FiltroTiendas
            selected={filters.store}
            onChange={(val) => onFilterChange("store", val)}
          />

          <hr className="border-gray-100" />

          <FiltroTipoRopa
            selected={filters.clothingType || []}
            onChange={(val) => onFilterChange("clothingType", val)}
          />

          <hr className="border-gray-100" />

          <FiltroTallas
            selected={filters.size}
            onChange={(val) => onFilterChange("size", val)}
          />

          <hr className="border-gray-100" />

          <FiltroColores
            selected={filters.color}
            onChange={(val) => onFilterChange("color", val)}
          />

          <hr className="border-gray-100" />

          <FiltroPrecio
            minPrice={filters.minPrice}
            maxPrice={filters.maxPrice}
            onChange={({ min, max }) => {
              onFilterChange("minPrice", min);
              onFilterChange("maxPrice", max);
            }}
          />

          <BotonLimpiarFiltros hasFilters={hasFilters} onClick={onClearFilters} />
        </div>
      </aside>
    </>
  );
}

export default SidebarFiltros;
