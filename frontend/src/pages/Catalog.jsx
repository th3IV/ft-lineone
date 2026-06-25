import { useState, useEffect, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams } from "react-router-dom";
import { fetchProducts, setFilters, setPage, clearFilters } from "../store/productSlice";
import { openVtonModal } from "../store/uiSlice";
import ProductGrid from "../components/ProductGrid";
import SidebarFiltros from "../components/SidebarFiltros";

const GENDER_CATEGORY_MAP = {
  Mujer: ["mujer", "vestidos", "bolsos", "faldas"],
  Hombre: ["hombre"],
  Unisex: ["accesorios", "unisex"],
  Niños: ["nino"],
};

function Catalog() {
  const dispatch = useDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const { products, filters, pagination, loading } = useSelector((state) => state.products);

  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const params = {};
    params.page = pagination.page;
    params.limit = 20;
    dispatch(fetchProducts(params));
  }, [dispatch, pagination.page]);

  useEffect(() => {
    const storeParam = searchParams.get("store");
    if (storeParam) {
      dispatch(setFilters({ store: storeParam }));
    }
  }, [dispatch, searchParams]);

  const filteredProducts = useMemo(() => {
    let result = products;
    if (filters.store) {
      result = result.filter((p) => p.store?.toLowerCase() === filters.store.toLowerCase());
    }
    if (filters.size) {
      result = result.filter((p) => p.sizes?.includes(filters.size));
    }
    if (filters.color) {
      result = result.filter((p) => p.colors?.some((c) => c.toLowerCase() === filters.color.toLowerCase()));
    }
    if (filters.minPrice) {
      result = result.filter((p) => p.price >= Number(filters.minPrice));
    }
    if (filters.maxPrice) {
      result = result.filter((p) => p.price <= Number(filters.maxPrice));
    }
    if (filters.gender) {
      const validCategories = GENDER_CATEGORY_MAP[filters.gender] || [];
      if (validCategories.length > 0) {
        result = result.filter((p) => validCategories.includes(p.category?.toLowerCase()));
      }
    }
    if (filters.clothingType?.length > 0) {
      const types = filters.clothingType.map((t) => t.toLowerCase());
      result = result.filter((p) => types.includes(p.category?.toLowerCase()));
    }
    if (filters.query) {
      const q = filters.query.toLowerCase();
      result = result.filter(
        (p) =>
          p.name?.toLowerCase().includes(q) ||
          p.description?.toLowerCase().includes(q)
      );
    }
    return result;
  }, [products, filters]);

  const totalFiltered = filteredProducts.length;
  const totalPages = Math.ceil(totalFiltered / 20);
  const startIdx = (pagination.page - 1) * 20;
  const pagedProducts = filteredProducts.slice(startIdx, startIdx + 20);

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

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex gap-8">
        <SidebarFiltros
          isOpen={sidebarOpen}
          filters={filters}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearFilters}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-6">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden btn-outline text-sm !py-2 !px-4"
            >
              <svg className="w-4 h-4 inline mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              Filtros
            </button>

            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar productos..."
                  className="w-full border border-gray-200 rounded-xl pl-10 pr-4 py-2.5 text-sm bg-white focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all"
                />
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </form>
          </div>

          <ProductGrid products={pagedProducts} loading={loading} onTryOn={handleTryOn} />

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-8">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="px-4 py-2 border border-gray-200 rounded-xl text-sm disabled:opacity-40 hover:border-fashion-pink transition-all"
              >
                Anterior
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  className={`w-9 h-9 rounded-xl text-sm font-medium transition-all ${
                    pagination.page === page
                      ? "bg-gradient-to-r from-fashion-pink to-fashion-purple text-white shadow-md"
                      : "border border-gray-200 text-gray-600 hover:border-fashion-pink"
                  }`}
                >
                  {page}
                </button>
              ))}
              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= totalPages}
                className="px-4 py-2 border border-gray-200 rounded-xl text-sm disabled:opacity-40 hover:border-fashion-pink transition-all"
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
