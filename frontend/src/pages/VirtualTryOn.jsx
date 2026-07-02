import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { motion } from "framer-motion";
import { Clock } from "lucide-react";
import { fetchProducts } from "../store/productSlice";
import { uploadImage, requestTryOn } from "../services/vton";
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

  const selectedProduct = products.find(
    (p) => String(p.id) === selectedProductId
  );

  const handleUserImageUpload = (dataUrl, file) => {
    setUserImage(dataUrl);
    setUserFile(file);
    setResultImage(null);
    setError("");
  };

  const handleGenerate = async () => {
    if (!userImage || !selectedProductId) return;
    setLoading(true);
    setError("");
    try {
      const uploadRes = await uploadImage(userImage);
      if (!uploadRes.image_url) {
        throw new Error("No se pudo subir la imagen. Intenta con otra foto.");
      }

      const res = await requestTryOn(selectedProductId, uploadRes.image_url);

      const imageUrl = res.output_image_url;
      if (!imageUrl) {
        throw new Error("No se pudo generar el resultado. Intenta con otra foto.");
      }

      setResultImage(imageUrl);

      const entry = {
        id: Date.now(),
        productId: selectedProductId,
        productName: selectedProduct?.name,
        resultImage: imageUrl,
        timestamp: new Date().toISOString(),
      };
      const updated = [entry, ...history].slice(0, 10);
      setHistory(updated);
      localStorage.setItem("tryOnHistory", JSON.stringify(updated));
    } catch (err) {
      console.error("Try-On failed:", err);
      const detail = err.response?.data?.detail;
      if (detail) {
        setError(detail);
      } else if (err.message?.includes("network") || err.message?.includes("fetch")) {
        setError("Error de conexion. Verifica tu internet y vuelve a intentar.");
      } else {
        setError(err.message || "Try-on failed. Please try again.");
      }
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
