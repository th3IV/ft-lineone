import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchProductById } from "../store/productSlice";
import { fetchRecommendations } from "../store/recommendationSlice";
import { openVtonModal } from "../store/uiSlice";
import ProductGrid from "../components/ProductGrid";

function ProductDetail() {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { selectedProduct, loading } = useSelector((state) => state.products);
  const { recommendations } = useSelector((state) => state.recommendations);
  const [selectedSize, setSelectedSize] = useState("");
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    dispatch(fetchProductById(id));
    dispatch(fetchRecommendations(id));
  }, [dispatch, id]);

  useEffect(() => {
    if (selectedProduct) {
      setSelectedSize(selectedProduct.sizes?.[0] || "");
      setSelectedColor(selectedProduct.colors?.[0] || "");
    }
  }, [selectedProduct]);

  const handleTryOn = () => {
    if (selectedProduct) {
      dispatch(openVtonModal(selectedProduct));
    }
  };

  const handleRecommendationTryOn = (product) => {
    dispatch(openVtonModal(product));
  };

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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <div className="aspect-square rounded-xl overflow-hidden bg-gray-100 mb-4">
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
                  className={`w-20 h-20 rounded-lg overflow-hidden border-2 flex-shrink-0 ${
                    selectedImage === idx ? "border-indigo-600" : "border-transparent"
                  }`}
                >
                  <img src={img} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <span className="text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
            {selectedProduct.store}
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mt-3">{selectedProduct.name}</h1>
          <p className="text-2xl font-bold text-gray-900 mt-2">
            {selectedProduct.currency || "$"}{selectedProduct.price?.toFixed(2)}
          </p>
          <p className="text-gray-600 mt-4">{selectedProduct.description}</p>

          {selectedProduct.sizes && selectedProduct.sizes.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Size</h3>
              <div className="flex flex-wrap gap-2">
                {selectedProduct.sizes.map((size) => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`px-4 py-2 border rounded-lg text-sm ${
                      selectedSize === size
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-gray-300 hover:border-gray-400"
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
                    className={`px-4 py-2 border rounded-lg text-sm ${
                      selectedColor === color
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-gray-300 hover:border-gray-400"
                    }`}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleTryOn}
            className="w-full mt-8 btn-primary text-lg py-3"
          >
            Probar ahora
          </button>
        </div>
      </div>

      {recommendations.length > 0 && (
        <section className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">AI Recommendations</h2>
          <ProductGrid
            products={recommendations}
            loading={false}
            onTryOn={handleRecommendationTryOn}
          />
        </section>
      )}
    </div>
  );
}

export default ProductDetail;
