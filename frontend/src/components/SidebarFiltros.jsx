import { X } from "lucide-react";
import FiltroGenero from "./FiltroGenero";
import FiltroTiendas from "./FiltroTiendas";
import FiltroTipoRopa from "./FiltroTipoRopa";
import FiltroTallas from "./FiltroTallas";
import FiltroColores from "./FiltroColores";
import FiltroPrecio from "./FiltroPrecio";
import FiltroOrden from "./FiltroOrden";
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
    filters.query ||
    filters.sort;

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-editorial-black/20 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => onFilterChange("_toggle", null)}
        />
      )}

      <aside
        className={`fixed lg:sticky top-14 lg:top-[72px] left-0 z-40 lg:z-0 h-[calc(100vh-3.5rem)] lg:h-[calc(100vh-72px)] w-72 bg-editorial-white lg:bg-transparent border-r border-editorial-black/5 lg:border-none overflow-y-auto transform transition-transform duration-300 lg:transform-none ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        } ${isOpen ? "shadow-[20px_0_60px_rgba(0,0,0,0.1)] lg:shadow-none" : ""}`}
      >
        <div className="p-6 space-y-6">
          {/* Mobile Header */}
          <div className="flex items-center justify-between lg:hidden">
            <h3 className="font-display text-base font-semibold text-editorial-black">
              Filtros
            </h3>
            <button
              onClick={() => onFilterChange("_toggle", null)}
              className="p-1.5 text-editorial-gray hover:text-editorial-black rounded-lg hover:bg-editorial-black/5 transition-all"
            >
              <X size={18} />
            </button>
          </div>

          <FiltroGenero
            selected={filters.gender}
            onChange={(val) => onFilterChange("gender", val)}
          />

          <div className="border-t border-editorial-black/5" />

          <FiltroTiendas
            selected={filters.store}
            onChange={(val) => onFilterChange("store", val)}
          />

          <div className="border-t border-editorial-black/5" />

          <FiltroTipoRopa
            selected={filters.clothingType || []}
            onChange={(val) => onFilterChange("clothingType", val)}
          />

          <div className="border-t border-editorial-black/5" />

          <FiltroTallas
            selected={filters.size}
            onChange={(val) => onFilterChange("size", val)}
          />

          <div className="border-t border-editorial-black/5" />

          <FiltroColores
            selected={filters.color}
            onChange={(val) => onFilterChange("color", val)}
          />

          <div className="border-t border-editorial-black/5" />

          <FiltroPrecio
            minPrice={filters.minPrice}
            maxPrice={filters.maxPrice}
            onChange={({ min, max }) => {
              onFilterChange("minPrice", min);
              onFilterChange("maxPrice", max);
            }}
          />

          <div className="border-t border-editorial-black/5" />

          <FiltroOrden
            selected={filters.sort}
            onChange={(val) => onFilterChange("sort", val)}
          />

          <BotonLimpiarFiltros hasFilters={hasFilters} onClick={onClearFilters} />
        </div>
      </aside>
    </>
  );
}

export default SidebarFiltros;
