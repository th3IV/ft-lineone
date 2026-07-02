import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchProducts } from "../store/productSlice";
import { requestTryOn } from "../services/vton";
import VirtualMirror from "../components/VirtualMirror";

function VirtualTryOn() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { products } = useSelector((state) => state.products);

  const [selectedProductId, setSelectedProductId] = useState(searchParams.get("product") || "");
  const [userImage, setUserImage] = useState(null);
  const [userFile, setUserFile] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    dispatch(fetchProducts({ limit: 50 }));
    const saved = localStorage.getItem("tryOnHistory");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch {}
    }
  }, [dispatch]);

  const selectedProduct = products.find((p) => String(p.id) === selectedProductId);

  const handleUserImageUpload = (dataUrl, file) => {
    setUserImage(dataUrl);
    setUserFile(file);
    setResultImage(null);
  };

  const handleGenerate = async () => {
    if (!userFile || !selectedProductId) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("user_image", userFile);
      formData.append("product_id", selectedProductId);
      const result = await requestTryOn(formData);
      setResultImage(result.output_image_url);
      const entry = {
        id: Date.now(),
        productId: selectedProductId,
        productName: selectedProduct?.name,
        resultImage: result.output_image_url,
        timestamp: new Date().toISOString(),
      };
      const updated = [entry, ...history].slice(0, 10);
      setHistory(updated);
      localStorage.setItem("tryOnHistory", JSON.stringify(updated));
    } catch (err) {
      console.error("Try-On failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadFromHistory = (entry) => {
    setSelectedProductId(String(entry.productId));
    setResultImage(entry.resultImage);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Virtual Try-On</h1>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Product</label>
        <select
          value={selectedProductId}
          onChange={(e) => {
            setSelectedProductId(e.target.value);
            setResultImage(null);
          }}
          className="w-full max-w-md border border-gray-300 rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">Choose a product...</option>
          {products.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} - {p.store}
            </option>
          ))}
        </select>
      </div>

      <VirtualMirror
        userImage={userImage}
        productImage={selectedProduct?.image_url}
        resultImage={resultImage}
        loading={loading}
        onUserImageUpload={handleUserImageUpload}
        onGenerate={handleGenerate}
      />

      {history.length > 0 && (
        <section className="mt-12">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Try-On History</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
            {history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => loadFromHistory(entry)}
                className="aspect-square rounded-lg overflow-hidden bg-gray-100 border-2 border-transparent hover:border-indigo-600 transition-colors"
              >
                <img
                  src={entry.resultImage}
                  alt={entry.productName}
                  className="w-full h-full object-cover"
                />
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default VirtualTryOn;
