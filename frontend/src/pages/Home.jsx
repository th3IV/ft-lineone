import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { fetchProducts } from "../store/productSlice";
import { openVtonModal } from "../store/uiSlice";
import ProductGrid from "../components/ProductGrid";

const stores = [
  { name: "Falabella", color: "bg-green-600" },
  { name: "Ripley", color: "bg-red-600" },
  { name: "Paris", color: "bg-blue-600" },
  { name: "Maui", color: "bg-teal-500" },
  { name: "Zara", color: "bg-black" },
];

function Home() {
  const dispatch = useDispatch();
  const { products, loading } = useSelector((state) => state.products);

  useEffect(() => {
    dispatch(fetchProducts({ limit: 8 }));
  }, [dispatch]);

  const handleTryOn = (product) => {
    dispatch(openVtonModal(product));
  };

  return (
    <div>
      <section className="bg-gradient-to-br from-fashion-pink to-fashion-purple text-white">
        <div className="max-w-7xl mx-auto px-4 py-20 sm:py-28">
          <div className="text-center">
            <h1 className="text-4xl sm:text-6xl font-bold mb-4">
              FT. THE LINE ONE
            </h1>
            <p className="text-xl sm:text-2xl text-white/80 mb-8">
              Try before you buy. Virtual fashion at your fingertips.
            </p>
            <Link
              to="/virtual-try-on"
              className="inline-block bg-white text-fashion-pink px-8 py-3 rounded-full text-lg font-semibold hover:bg-fashion-pink-light transition-colors"
            >
              Try Virtual Try-On
            </Link>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Featured Products</h2>
        <ProductGrid products={products} loading={loading} onTryOn={handleTryOn} />
      </section>

      <section className="bg-fashion-pink-light py-12">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">Our Stores</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {stores.map((store) => (
              <Link
                key={store.name}
                to={`/catalog?store=${store.name.toLowerCase()}`}
                className={`${store.color} text-white px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity`}
              >
                {store.name}
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
