import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import { fetchProducts } from "../store/productSlice";
import { addItem, removeItem, clearOutfit } from "../store/outfitSlice";

const categories = [
  { id: "poleras", name: "Poleras", icon: "👕" },
  { id: "polerones", name: "Polerones", icon: "🧥" },
  { id: "pantalones", name: "Pantalones", icon: "👖" },
  { id: "chaquetas", name: "Chaquetas", icon: "🧥" },
  { id: "faldas", name: "Faldas", icon: "👗" },
  { id: "vestidos", name: "Vestidos", icon: "👗" },
  { id: "zapatos", name: "Zapatos", icon: "👟" },
  { id: "accesorios", name: "Accesorios", icon: "👜" },
];

function OutfitBuilder() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { products, loading } = useSelector((state) => state.products);
  const outfitItems = useSelector((state) => state.outfit.items);
  const [activeCategory, setActiveCategory] = useState("poleras");

  useEffect(() => {
    dispatch(fetchProducts({ limit: 50 }));
  }, [dispatch]);

  const filteredProducts = products.filter((p) => {
    const cat = (p.category || "").toLowerCase();
    return cat.includes(activeCategory) || cat.includes(activeCategory.slice(0, -1));
  });

  const handleAddItem = (product) => {
    const exists = outfitItems.find((item) => item.id === product.id);
    if (!exists) {
      dispatch(addItem(product));
    }
  };

  const handleRemoveItem = (id) => {
    dispatch(removeItem(id));
  };

  const handleTryOnOutfit = () => {
    if (outfitItems.length > 0) {
      navigate(`/virtual-try-on?product=${outfitItems[0].id}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Armador de Outfits</h1>
          <p className="text-gray-500 mt-1">Arma tu look perfecto combinando prendas</p>
        </div>
        {outfitItems.length > 0 && (
          <div className="flex gap-3">
            <button
              onClick={() => dispatch(clearOutfit())}
              className="px-4 py-2 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50"
            >
              Limpiar
            </button>
            <button
              onClick={handleTryOnOutfit}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
            >
              Probar Outfit
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-3">
          <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm whitespace-nowrap transition-colors ${
                  activeCategory === cat.id
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                <span>{cat.icon}</span>
                {cat.name}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-gray-400 text-lg">No hay productos en esta categoría</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {filteredProducts.map((product) => {
                const isAdded = outfitItems.find((item) => item.id === product.id);
                return (
                  <div key={product.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow">
                    <Link to={`/product/${product.id}`}>
                      <div className="aspect-square bg-gray-100">
                        <img
                          src={product.image_url || "/placeholder.jpg"}
                          alt={product.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </Link>
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                          {product.store}
                        </span>
                        <span className="text-xs text-gray-400">{product.currency || "$"}{product.price?.toFixed(0)}</span>
                      </div>
                      <Link to={`/product/${product.id}`}>
                        <h3 className="text-sm font-medium text-gray-900 truncate">{product.name}</h3>
                      </Link>
                      <button
                        onClick={() => isAdded ? handleRemoveItem(product.id) : handleAddItem(product)}
                        className={`w-full mt-2 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                          isAdded
                            ? "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100"
                            : "bg-indigo-600 text-white hover:bg-indigo-700"
                        }`}
                      >
                        {isAdded ? "Quitar" : "Agregar al outfit"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-gray-200 p-4 sticky top-24">
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              Tu Outfit ({outfitItems.length})
            </h2>

            {outfitItems.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <svg className="mx-auto h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p className="text-sm">Agrega prendas para armar tu outfit</p>
              </div>
            ) : (
              <div className="space-y-3">
                {outfitItems.map((item) => (
                  <div key={item.id} className="flex items-center gap-3 bg-gray-50 rounded-lg p-2">
                    <div className="w-12 h-12 rounded-lg bg-gray-200 overflow-hidden flex-shrink-0">
                      <img src={item.image_url || "/placeholder.jpg"} alt="" className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-900 truncate">{item.name}</p>
                      <p className="text-xs text-gray-500">{item.store} - {item.currency || "$"}{item.price?.toFixed(0)}</p>
                    </div>
                    <button onClick={() => handleRemoveItem(item.id)} className="text-gray-400 hover:text-red-500 flex-shrink-0">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default OutfitBuilder;
