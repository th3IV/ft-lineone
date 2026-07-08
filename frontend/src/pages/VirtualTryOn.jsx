import { useState, useEffect, useMemo, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { motion } from "framer-motion";
import { Clock } from "lucide-react";
import { fetchProducts } from "../store/productSlice";
import { useVtonPolling } from "../hooks/useVtonPolling";
import VirtualMirror from "../components/VirtualMirror";
import RevealOnScroll from "../components/RevealOnScroll";
import { useFeatureGate } from "../hooks/useFeatureGate";
import PremiumBanner from "../components/PremiumBanner";
import UpgradeModal from "../components/UpgradeModal";

function VirtualTryOn() {
  const [searchParams, setSearchParams] = useSearchParams();
  const dispatch = useDispatch();
  const { products } = useSelector((state) => state.products);
  const { isAuthenticated } = useSelector((state) => state.user);
  const { isPremium, showUpgrade, showUpgradeModal, hideUpgradeModal, handleUpgrade } = useFeatureGate();

  const [selectedProductId, setSelectedProductId] = useState(
    searchParams.get("product") || ""
  );
  const [userImage, setUserImage] = useState(null);
  const [history, setHistory] = useState([]);

  const { loading, error, resultImage, progress, generate, reset, setError } =
    useVtonPolling();

  useEffect(() => {
    dispatch(fetchProducts({ limit: 50 }));
    const saved = localStorage.getItem("tryOnHistory");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch {
        localStorage.removeItem("tryOnHistory");
      }
    }
  }, [dispatch]);

  const selectedProduct = useMemo(
    () => products.find((p) => String(p.id) === selectedProductId),
    [products, selectedProductId]
  );

  const handleSelectProduct = useCallback(
    (productId) => {
      setSelectedProductId(productId);
      reset();
      if (productId) {
        setSearchParams({ product: productId }, { replace: true });
      } else {
        setSearchParams({}, { replace: true });
      }
    },
    [reset, setSearchParams]
  );

  const handleUserImageUpload = useCallback(
    (dataUrl) => {
      setUserImage(dataUrl);
      reset();
    },
    [reset]
  );

  const handleGenerate = useCallback(async () => {
    if (!userImage || !selectedProductId) return;
    if (!isAuthenticated) {
      setError("Debes iniciar sesion para usar el Try-On.");
      return;
    }

    const imageUrl = await generate(selectedProductId, userImage, selectedProduct?.image_url);

    if (imageUrl) {
      const entry = {
        id: Date.now(),
        productId: selectedProductId,
        productName: selectedProduct?.name,
        resultImage: imageUrl,
        timestamp: new Date().toISOString(),
      };
      setHistory((prev) => {
        const updated = [entry, ...prev].slice(0, 5);
        localStorage.setItem("tryOnHistory", JSON.stringify(updated));
        return updated;
      });
    }
  }, [
    userImage,
    selectedProductId,
    isAuthenticated,
    generate,
    selectedProduct,
  ]);

  const loadFromHistory = useCallback(
    (entry) => {
      handleSelectProduct(String(entry.productId));
    },
    [handleSelectProduct]
  );

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

      {!isPremium && <PremiumBanner onUpgrade={showUpgradeModal} />}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mb-8"
      >
        <label className="editorial-label block mb-3">Seleccionar prenda</label>
        <select
          value={selectedProductId}
          onChange={(e) => handleSelectProduct(e.target.value)}
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

      {loading && progress.elapsed > 0 && (
        <div className="mb-6 p-3 bg-editorial-cream border border-editorial-black/10 rounded-xl text-sm text-editorial-gray">
          Generando... ({progress.elapsed}s transcurridos)
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
      <UpgradeModal isOpen={showUpgrade} onClose={hideUpgradeModal} onUpgrade={handleUpgrade} />
    </div>
  );
}

export default VirtualTryOn;
