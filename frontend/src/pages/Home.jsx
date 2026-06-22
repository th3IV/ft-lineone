import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import { fetchProducts, searchProducts } from "../store/productSlice";

const categories = [
  { id: "poleras", name: "Poleras", icon: "👕", color: "bg-blue-100 text-blue-600" },
  { id: "polerones", name: "Polerones", icon: "🧥", color: "bg-gray-100 text-gray-600" },
  { id: "pantalones", name: "Pantalones", icon: "👖", color: "bg-indigo-100 text-indigo-600" },
  { id: "chaquetas", name: "Chaquetas", icon: "🧥", color: "bg-amber-100 text-amber-600" },
  { id: "faldas", name: "Faldas", icon: "👗", color: "bg-pink-100 text-pink-600" },
  { id: "vestidos", name: "Vestidos", icon: "👗", color: "bg-rose-100 text-rose-600" },
  { id: "zapatos", name: "Zapatos", icon: "👟", color: "bg-green-100 text-green-600" },
  { id: "accesorios", name: "Accesorios", icon: "👜", color: "bg-purple-100 text-purple-600" },
];

const stores = [
  { name: "Falabella", color: "bg-green-600", url: "https://www.falabella.com" },
  { name: "Ripley", color: "bg-red-600", url: "https://www.ripley.com" },
  { name: "Paris", color: "bg-blue-600", url: "https://www.paris.cl" },
  { name: "Maui", color: "bg-teal-500", url: "https://www.maui.cl" },
  { name: "Zara", color: "bg-black", url: "https://www.zara.com" },
];

function Home() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { products, loading } = useSelector((state) => state.products);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    dispatch(fetchProducts({ limit: 12 }));
  }, [dispatch]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/catalog?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleCategoryClick = (catId) => {
    navigate(`/catalog?category=${catId}`);
  };

  return (
    <div>
      <section className="bg-gradient-to-br from-gray-900 via-gray-800 to-indigo-900 text-white">
        <div className="max-w-7xl mx-auto px-4 py-16 sm:py-24">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl sm:text-6xl font-bold mb-4 tracking-tight">
              FT. THE LINE ONE
            </h1>
            <p className="text-lg sm:text-xl text-gray-300 mb-8">
              Encuentra las mejores ofertas de ropa y pruébatelas virtualmente antes de comprar
            </p>
            <form onSubmit={handleSearch} className="max-w-xl mx-auto">
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Busca poleras, pantalones, chaquetas..."
                  className="w-full pl-12 pr-4 py-4 rounded-xl text-gray-900 text-base focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
                <svg className="absolute left-4 top-4 h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </form>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 -mt-8">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => handleCategoryClick(cat.id)}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl ${cat.color} hover:shadow-lg transition-all hover:-translate-y-1`}
            >
              <span className="text-2xl">{cat.icon}</span>
              <span className="text-xs font-medium whitespace-nowrap">{cat.name}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Ofertas Destacadas</h2>
          <Link to="/catalog" className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
            Ver todo →
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {products.slice(0, 12).map((product) => (
              <div key={product.id} className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-all hover:-translate-y-1">
                <Link to={`/product/${product.id}`}>
                  <div className="aspect-[3/4] bg-gray-100 overflow-hidden relative">
                    <img
                      src={product.image_url || "/placeholder.jpg"}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    {product.discount && (
                      <span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded">
                        -{product.discount}%
                      </span>
                    )}
                  </div>
                </Link>
                <div className="p-3">
                  <span className="text-xs text-indigo-600 font-medium">{product.store}</span>
                  <Link to={`/product/${product.id}`}>
                    <h3 className="text-sm font-medium text-gray-900 truncate mt-0.5">{product.name}</h3>
                  </Link>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-base font-bold text-gray-900">
                      {product.currency || "$"}{product.price?.toFixed(0)}
                    </span>
                    {product.original_price && (
                      <span className="text-xs text-gray-400 line-through">
                        {product.currency || "$"}{product.original_price?.toFixed(0)}
                      </span>
                    )}
                  </div>
                  <Link
                    to={`/virtual-try-on?product=${product.id}`}
                    className="block mt-2 text-center text-xs bg-indigo-600 text-white py-1.5 rounded-lg hover:bg-indigo-700 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    Probar ahora
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">Tiendas Disponibles</h2>
          <p className="text-gray-500 text-center mb-8 max-w-2xl mx-auto">
            Comparamos precios en las mejores tiendas para que encuentres siempre el mejor precio
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {stores.map((store) => (
              <a
                key={store.name}
                href={store.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`${store.color} text-white px-6 py-4 rounded-xl font-medium hover:opacity-90 transition-opacity text-center flex flex-col items-center gap-1`}
              >
                <span className="text-lg font-bold">{store.name}</span>
                <span className="text-xs opacity-75">Ver ofertas →</span>
              </a>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-indigo-600 py-16">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Pruébate la ropa virtualmente</h2>
          <p className="text-indigo-100 mb-8 max-w-2xl mx-auto">
            Sube una foto tuya y mira cómo te queda cualquier prenda antes de comprarla.
            Dile adiós a las devoluciones.
          </p>
          <Link
            to="/virtual-try-on"
            className="inline-block bg-white text-indigo-600 px-8 py-3 rounded-full text-lg font-semibold hover:bg-indigo-50 transition-colors"
          >
            Probar Probador Virtual
          </Link>
        </div>
      </section>

      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          <p className="font-bold text-white text-lg mb-2">FT. THE LINE ONE</p>
          <p>Comparador de precios de moda con probador virtual IA</p>
          <p className="mt-2">© 2026 FT. THE LINE ONE. Todos los derechos reservados.</p>
        </div>
      </footer>
    </div>
  );
}

export default Home;
