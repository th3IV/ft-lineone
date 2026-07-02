import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { motion } from "framer-motion";
import { Sparkles, Clock } from "lucide-react";
import { fetchProducts } from "../store/productSlice";
import { requestTryOn } from "../services/vton";
import VirtualMirror from "../components/VirtualMirror";
import RevealOnScroll from "../components/RevealOnScroll";

function VirtualTryOn() {
  const [searchParams] = useSearchParams();
  const dispatch = useDispatch();
  const { products } = useSelector((state) => state.products);

  const [selectedProductId, setSelectedProductId] = useState(
    searchParams.get("product") || ""
  );
  const [userImage, setUserImage] = useState(null);
  const [userFile, setUserFile] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [resultBlobUrl, setResultBlobUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
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

  useEffect(() => {
    return () => {
      if (resultBlobUrl) URL.revokeObjectURL(resultBlobUrl);
    };
  }, [resultBlobUrl]);

  const selectedProduct = products.find(
    (p) => String(p.id) === selectedProductId
  );

  const handleUserImageUpload = (dataUrl, file) => {
    setUserImage(dataUrl);
    setUserFile(file);
    setResultImage(null);
    setError("");
  };

  const blobToBase64 = (blob) =>
    new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });

  const handleGenerate = async () => {
    if (!userFile || !selectedProductId) return;
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("user_image", userFile);
      formData.append("product_id", selectedProductId);
      const blob = await requestTryOn(formData);

      if (resultBlobUrl) URL.revokeObjectURL(resultBlobUrl);
      const url = URL.createObjectURL(blob);
      setResultBlobUrl(url);
      setResultImage(url);

      const base64 = await blobToBase64(blob);
      const entry = {
        id: Date.now(),
        productId: selectedProductId,
        productName: selectedProduct?.name,
        resultImage: base64,
        timestamp: new Date().toISOString(),
      };
      const updated = [entry, ...history].slice(0, 10);
      setHistory(updated);
      localStorage.setItem("tryOnHistory", JSON.stringify(updated));
    } catch (err) {
      console.error("Try-On failed:", err);
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Try-on failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadFromHistory = (entry) => {
    setSelectedProductId(String(entry.productId));
    setResultImage(entry.resultImage);
  };

  return (
    <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <p className="editorial-label mb-3">Virtual Try-On</p>
        <h1 className="section-title mb-10">
          Prueba cualquier prenda con IA
        </h1>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mb-8"
      >
        <label className="editorial-label block mb-3">Seleccionar prenda</label>
        <select
          value={selectedProductId}
          onChange={(e) => {
            setSelectedProductId(e.target.value);
            setResultImage(null);
            setError("");
          }}
          className="w-full max-w-md border-b border-editorial-black/10 rounded-none px-0 py-3 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
        >
          <option value="">Elige una prenda...</option>
          {products.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} - {p.store}
            </option>
          ))}
        </select>
      </motion.div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
          {error}
        </div>
      )}

      <VirtualMirror
        userImage={userImage}
        productImage={selectedProduct?.image_url}
        resultImage={resultImage}
        loading={loading}
        onUserImageUpload={handleUserImageUpload}
        onGenerate={handleGenerate}
      />

      {history.length > 0 && (
        <RevealOnScroll className="mt-16">
          <div className="flex items-center gap-2 mb-6">
            <Clock size={16} className="text-editorial-gray" />
            <h2 className="text-lg font-display font-semibold text-editorial-black">
              Historial
            </h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            {history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => loadFromHistory(entry)}
                className="aspect-[3/4] rounded-xl overflow-hidden bg-editorial-cream-dark border border-editorial-black/5 hover:border-editorial-black/20 transition-all duration-200 group"
              >
                <img
                  src={entry.resultImage}
                  alt={entry.productName}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
              </button>
            ))}
          </div>
        </RevealOnScroll>
      )}
    </div>
  );
}

export default VirtualTryOn;
