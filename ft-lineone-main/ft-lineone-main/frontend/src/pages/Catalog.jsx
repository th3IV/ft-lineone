import { useState, useEffect, useCallback } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams } from "react-router-dom";
import { fetchProducts, setFilters } from "../store/productSlice";
import ProductGrid from "../components/ProductGrid";

const stores = ["Falabella", "Ripley", "Paris", "Maui", "Zara"];
const categories = ["Clothing", "Shoes", "Accessories", "Sportswear", "Formal"];

function Catalog() {
  const dispatch = useDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const { products, filters, pagination, loading } = useSelector((state) => state.products);

  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    const params = {};
    if (filters.store) params.store = filters.store;
    if (filters.category) params.category = filters.category;
    if (filters.minPrice) params.min_price = filters.minPrice;
    if (filters.maxPrice) params.max_price = filters.maxPrice;
    if (filters.query) params.q = filters.query;
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

  const handleStoreFilter = (store) => {
    dispatch(setFilters({ store: filters.store === store ? null : store, page: 1 }));
  };

  const handleCategoryFilter = (category) => {
    dispatch(setFilters({ category: filters.category === category ? null : category, page: 1 }));
  };

  const handlePriceChange = (min, max) => {
    dispatch(setFilters({ minPrice: min, maxPrice: max, page: 1 }));
  };

  const handlePageChange = (page) => {
    dispatch(setFilters({ page }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleTryOn = (product) => {
    window.location.href = `/virtual-try-on?product=${product.id}`;
  };

  const totalPages = Math.ceil((pagination.total || 0) / 20);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col lg:flex-row gap-8">
        <aside className="lg:w-64 flex-shrink-0">
          <div className="lg:hidden mb-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-left"
            >
              {showFilters ? "Hide Filters" : "Show Filters"}
            </button>
          </div>
          <div className={`${showFilters ? "block" : "hidden"} lg:block space-y-6`}>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">Stores</h3>
              <div className="space-y-2">
                {stores.map((store) => (
                  <button
                    key={store}
                    onClick={() => handleStoreFilter(store.toLowerCase())}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      filters.store === store.toLowerCase()
                        ? "bg-indigo-50 text-indigo-700 font-medium"
                        : "text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    {store}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">Categories</h3>
              <div className="space-y-2">
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={() => handleCategoryFilter(category.toLowerCase())}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      filters.category === category.toLowerCase()
                        ? "bg-indigo-50 text-indigo-700 font-medium"
                        : "text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">Price Range</h3>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.minPrice || ""}
                  onChange={(e) => handlePriceChange(e.target.value || null, filters.maxPrice)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                />
                <span className="text-gray-400">-</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.maxPrice || ""}
                  onChange={(e) => handlePriceChange(filters.minPrice, e.target.value || null)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                />
              </div>
            </div>
          </div>
        </aside>

        <div className="flex-1">
          <form onSubmit={handleSearch} className="mb-6">
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products..."
                className="w-full border border-gray-300 rounded-lg pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <svg
                className="absolute left-3 top-3.5 h-5 w-5 text-gray-400"
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </form>

          <ProductGrid products={products} loading={loading} onTryOn={handleTryOn} />

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-8">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50"
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  className={`px-4 py-2 border rounded-lg text-sm ${
                    pagination.page === page
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "hover:bg-gray-50"
                  }`}
                >
                  {page}
                </button>
              ))}
              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= totalPages}
                className="px-4 py-2 border rounded-lg text-sm disabled:opacity-50 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Catalog;
