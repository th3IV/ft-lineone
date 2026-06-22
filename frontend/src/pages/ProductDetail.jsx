import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchProductById } from "../store/productSlice";
import { addItem } from "../store/outfitSlice";
import { getPriceComparison } from "../services/api";

function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { selectedProduct, loading } = useSelector((state) => state.products);
  const [selectedSize, setSelectedSize] = useState("");
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedImage, setSelectedImage] = useState(0);
  const [priceComparison, setPriceComparison] = useState(null);
  const [priceLoading, setPriceLoading] = useState(false);

  useEffect(() => {
    dispatch(fetchProductById(id));
  }, [dispatch, id]);

  useEffect(() => {
    if (selectedProduct) {
      setSelectedSize(selectedProduct.sizes?.[0] || "");
      setSelectedColor(selectedProduct.colors?.[0] || "");
      loadPriceComparison();
    }
  }, [selectedProduct]);

  const loadPriceComparison = async () => {
    setPriceLoading(true);
    try {
      const data = await getPriceComparison(id);
      setPriceComparison(data);
    } catch {
      setPriceComparison(null);
    } finally {
      setPriceLoading(false);
    }
  };

  const handleTryOn = () => {
    navigate(`/virtual-try-on?product=${id}`);
  };

  const handleAddToOutfit = () => {
    if (selectedProduct) {
      dispatch(addItem(selectedProduct));
    }
  };

  const matches = priceComparison?.matches || [];
  const sorted = [...matches].sort((a, b) => a.price - b.price);
  const cheapest = sorted[0];
  const currentStorePrice = selectedProduct
    ? { store: selectedProduct.store, price: selectedProduct.price, url: "#" }
    : null;

  if (loading || !selectedProduct) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const images = selectedProduct.images || [selectedProduct.image_url];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <nav className="text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-indigo-600">Inicio</Link>
        <span className="mx-2">/</span>
        <Link to="/catalog" className="hover:text-indigo-600">Catálogo</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{selectedProduct.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <div className="aspect-[3/4] rounded-xl overflow-hidden bg-gray-100 mb-4">
            <img
              src={images[selectedImage]}
              alt={selectedProduct.name}
              className="w-full h-full object-cover"
            />
          </div>
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`w-20 h-20 rounded-lg overflow-hidden border-2 flex-shrink-0 transition-colors ${
                    selectedImage === idx ? "border-indigo-600" : "border-transparent hover:border-gray-300"
                  }`}
                >
                  <img src={img} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <span className="inline-block text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full mb-3">
            {selectedProduct.store}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">{selectedProduct.name}</h1>

          <div className="flex items-baseline gap-3 mt-3">
            <p className="text-3xl font-bold text-gray-900">
              {selectedProduct.currency || "$"}{selectedProduct.price?.toFixed(0)}
            </p>
            {selectedProduct.original_price && (
              <p className="text-lg text-gray-400 line-through">
                {selectedProduct.currency || "$"}{selectedProduct.original_price?.toFixed(0)}
              </p>
            )}
            {selectedProduct.discount && (
              <span className="text-sm font-semibold text-red-500 bg-red-50 px-2 py-0.5 rounded">
                -{selectedProduct.discount}% OFF
              </span>
            )}
          </div>

          {cheapest && cheapest.store !== selectedProduct.store && (
            <div className="mt-2 bg-green-50 border border-green-200 rounded-lg px-4 py-2 text-sm">
              <span className="font-medium text-green-700">Mejor precio: </span>
              <span className="text-green-600">
                {cheapest.store} — ${cheapest.price.toLocaleString()}
                {cheapest.currency !== "CLP" && ` ${cheapest.currency}`}
              </span>
            </div>
          )}

          <p className="text-gray-600 mt-4">{selectedProduct.description}</p>

          {selectedProduct.sizes && selectedProduct.sizes.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Talla</h3>
              <div className="flex flex-wrap gap-2">
                {selectedProduct.sizes.map((size) => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`px-4 py-2 border rounded-lg text-sm font-medium transition-colors ${
                      selectedSize === size
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-gray-300 hover:border-gray-400 text-gray-700"
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          )}

          {selectedProduct.colors && selectedProduct.colors.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Color</h3>
              <div className="flex flex-wrap gap-2">
                {selectedProduct.colors.map((color) => (
                  <button
                    key={color}
                    onClick={() => setSelectedColor(color)}
                    className={`px-4 py-2 border rounded-lg text-sm font-medium transition-colors ${
                      selectedColor === color
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-gray-300 hover:border-gray-400 text-gray-700"
                    }`}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleTryOn}
              className="flex-1 bg-indigo-600 text-white py-3 rounded-xl text-lg font-semibold hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
              </svg>
              Probador Virtual
            </button>
            <button
              onClick={handleAddToOutfit}
              className="px-6 py-3 border-2 border-indigo-600 text-indigo-600 rounded-xl font-semibold hover:bg-indigo-50 transition-colors"
            >
              + Outfit
            </button>
          </div>

          <div className="mt-8 bg-gray-50 rounded-xl p-5">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Comparar Precios</h3>
            {priceLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
              </div>
            ) : sorted.length > 0 ? (
              <div className="space-y-3">
                {sorted.map((item, idx) => (
                  <div
                    key={`${item.store}-${item.id}`}
                    className={`flex items-center justify-between p-3 rounded-lg transition-colors cursor-default ${
                      idx === 0
                        ? "bg-green-50 border border-green-200"
                        : "bg-white border border-gray-200"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${idx === 0 ? "bg-green-500" : "bg-gray-300"}`}></div>
                      <div>
                        <span className="font-medium text-sm text-gray-900">{item.store}</span>
                        {item.last_checked && (
                          <p className="text-xs text-gray-500">
                            {new Date(item.last_checked).toLocaleDateString("es-CL", { day: "numeric", month: "short" })}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`font-bold ${idx === 0 ? "text-green-600 text-lg" : "text-gray-900"}`}>
                        ${item.price.toLocaleString()}
                      </span>
                      {idx === 0 && (
                        <p className="text-xs text-green-600 font-medium">Mejor precio</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-2">
                No hay otras tiendas con este producto aún. Vuelve pronto.
              </p>
            )}
            <p className="text-xs text-gray-400 mt-3 text-center">
              *Precios obtenidos automáticamente. Última actualización vía scraping periódico.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductDetail;
