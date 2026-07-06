import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams } from "react-router-dom";
import { Search, SlidersHorizontal } from "lucide-react";
import {
  fetchProducts,
  setFilters,
  setPage,
  clearFilters,
} from "../store/productSlice";
import { openVtonModal } from "../store/uiSlice";
import ProductGrid from "../components/ProductGrid";
import SidebarFiltros from "../components/SidebarFiltros";

function Catalog() {
  const dispatch = useDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const { products, filters, pagination, loading } = useSelector(
    (state) => state.products
  );

  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const params = {};
    if (filters.store) params.store = filters.store;
    if (filters.gender) params.gender = filters.gender;
    if (filters.clothingType?.length)
      params.clothing_type = filters.clothingType.join(",");
    if (filters.size) params.size = filters.size;
    if (filters.color) params.color = filters.color;
    if (filters.minPrice) params.min_price = filters.minPrice;
    if (filters.maxPrice) params.max_price = filters.maxPrice;
    if (filters.query) params.q = filters.query;
    if (filters.sort) params.sort = filters.sort;
    params.page = pagination.page;
    params.limit = 20;
    dispatch(fetchProducts(params));
  }, [dispatch, filters, pagination.page]);

  useEffect(() => {
    const storeParam = searchParams.get("store");
    if (storeParam) {
      dispatch(setFilters({ store: storeParam }));
    }
  }, [dispatch, searchParams]);

  const handleSearch = (e) => {
    e.preventDefault();
    dispatch(setFilters({ query: search, page: 1 }));
    if (search) {
      setSearchParams({ q: search });
    } else {
      setSearchParams({});
    }
  };

  const handleFilterChange = (key, value) => {
    if (key === "_toggle") {
      setSidebarOpen(!sidebarOpen);
      return;
    }
    dispatch(setFilters({ [key]: value, page: 1 }));
  };

  const handleClearFilters = () => {
    dispatch(clearFilters());
    setSearchParams({});
  };

  const handlePageChange = (page) => {
    dispatch(setPage(page));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleTryOn = (product) => {
    dispatch(openVtonModal(product));
  };

  const totalPages = Math.ceil((pagination.total || 0) / 20);

  return (
    <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-10">
      <div className="flex gap-8">
        <SidebarFiltros
          isOpen={sidebarOpen}
          filters={filters}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearFilters}
        />

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-4 mb-8">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden flex items-center gap-2 text-xs text-editorial-gray hover:text-editorial-black transition-colors"
            >
              <SlidersHorizontal size={16} />
              Filtros
            </button>

            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-0 top-1/2 -translate-y-1/2 text-editorial-gray-light"
                />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar productos..."
                  className="w-full border-b border-editorial-black/10 rounded-none pl-7 pr-4 py-2.5 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
                />
              </div>
            </form>
          </div>

          <ProductGrid
            products={products}
            loading={loading}
            onTryOn={handleTryOn}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-10">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="px-4 py-2 text-xs text-editorial-gray hover:text-editorial-black disabled:opacity-30 transition-colors"
              >
                Anterior
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                (page) => (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`w-8 h-8 rounded-full text-xs font-medium transition-all ${
                      pagination.page === page
                        ? "bg-editorial-black text-white"
                        : "text-editorial-gray hover:text-editorial-black"
                    }`}
                  >
                    {page}
                  </button>
                )
              )}
              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= totalPages}
                className="px-4 py-2 text-xs text-editorial-gray hover:text-editorial-black disabled:opacity-30 transition-colors"
              >
                Siguiente
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Catalog;
