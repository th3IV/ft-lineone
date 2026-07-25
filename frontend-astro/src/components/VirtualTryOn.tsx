import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Camera, X, RotateCcw, Download, Heart, Share2 } from "lucide-react";
import { Button } from "./ui/Button";
import { Modal } from "./ui/Modal";
import { Toast } from "./ui/Modal";
import { VirtualMirror } from "./VirtualMirror";
import { UpgradeModal } from "./UpgradeModal";
import { useVtonPolling } from "@/hooks/useVtonPolling";
import { useFeatureGate } from "@/hooks/useFeatureGate";
import { useSelector, useDispatch } from "react-redux";
import type { RootState, AppDispatch } from "@/store";
import { setUnauthorizedCallback } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
import { addToast } from "@/store/uiSlice";
import { setUser } from "@/store/userSlice";
import { fetchProducts } from "@/store/productSlice";

interface VirtualTryOnProps {
  productId?: string;
  initialProduct?: any;
}

export const VirtualTryOn = ({ productId, initialProduct }: VirtualTryOnProps) => {
  const dispatch = useDispatch<AppDispatch>();
  const { user, isAuthenticated } = useSelector((state: RootState) => state.user);
  const { items: products } = useSelector((state: RootState) => state.products);
  const { isPremium, showUpgrade, showUpgradeModal, hideUpgradeModal, handleUpgrade, upgradeLoading, upgradeError } = useFeatureGate();
  
  const [selectedProductId, setSelectedProductId] = useState(productId || "");
  const [userImage, setUserImage] = useState<string | null>(null);
  const [history, setHistory] = useState<Array<{ id: number; productId: string; productName: string; resultImage: string; timestamp: string }>>([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { loading, error: vtonError, resultImage, progress, generate, reset, setError: setVtonError } = useVtonPolling();

  useEffect(() => {
    setUnauthorizedCallback(() => {
      dispatch({ type: "user/logout" });
    });
  }, [dispatch]);

  // Load user profile (daily_usage, premium) — login page only stores tokens
  useEffect(() => {
    let cancelled = false;
    if (isAuthenticated && !user) {
      getCurrentUser()
        .then((u) => { if (!cancelled) dispatch(setUser(u)); })
        .catch(() => { /* token may be expired — interceptor handles 401 */ });
    }
    return () => { cancelled = true; };
  }, [isAuthenticated, user, dispatch]);

  // Load catalog products for the selector
  useEffect(() => {
    if (products.length === 0) {
      dispatch(fetchProducts({ page: 1, limit: 100, filters: {} }));
    }
  }, [products.length, dispatch]);

  useEffect(() => {
    const saved = localStorage.getItem("tryOnHistory");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch {
        localStorage.removeItem("tryOnHistory");
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("tryOnHistory", JSON.stringify(history));
  }, [history]);

  const selectedProduct = products.find((p) => p.id === selectedProductId) || initialProduct;

  const handleImageUpload = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("El archivo debe ser una imagen");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError("La imagen no debe superar 8MB");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setUserImage(e.target?.result as string);
      setError(null);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleImageUpload(file);
  };

  const handleGenerate = async () => {
    if (!userImage || !selectedProductId) {
      setError("Selecciona una prenda y sube tu foto");
      return;
    }
    if (!isAuthenticated) {
      dispatch(addToast({ message: "Debes iniciar sesión para usar el probador", type: "error" }));
      return;
    }
    if (!isPremium && user && user.daily_usage?.vton >= 5) {
      showUpgradeModal();
      return;
    }

    try {
      setError(null);
      const result = await generate(selectedProductId, userImage, selectedProduct?.image_url);
      if (result) {
        const entry = {
          id: Date.now(),
          productId: selectedProductId,
          productName: products.find(p => p.id === selectedProductId)?.name || "Producto",
          resultImage: result,
          timestamp: new Date().toISOString(),
        };
        setHistory((prev) => [entry, ...prev].slice(0, 5));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Error al generar la prueba virtual");
    }
  };

  const loadFromHistory = (entry: typeof history[0]) => {
    setSelectedProductId(entry.productId);
    setUserImage(entry.resultImage);
  };

  return (
    <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <p className="editorial-label mb-3">Virtual Try-On</p>
        <h1 className="section-title mb-10">Prueba cualquier prenda con IA</h1>
      </motion.div>

      {!isPremium && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 p-4 bg-editorial-cream border border-editorial-black/10 rounded-xl"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-editorial-gold/10 flex items-center justify-center">
                <svg className="w-5 h-5 text-editorial-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2m0 0v5.586a1 1 0 01-.293.707l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" />
                </svg>
              </div>
              <div>
                <p className="font-display font-semibold text-editorial-black">Prueba ilimitada con Premium</p>
                <p className="text-sm text-editorial-gray">Te quedan {5 - (user?.daily_usage?.vton || 0)} intentos gratis hoy</p>
              </div>
            </div>
            <Button variant="secondary" onClick={showUpgradeModal} size="sm">
              Hacerme Premium
            </Button>
          </div>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mb-8"
      >
        <label className="editorial-label block mb-3">Seleccionar prenda</label>
        <select
          value={selectedProductId}
          onChange={(e) => setSelectedProductId(e.target.value)}
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

      {(error || vtonError) && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm"
        >
          {error || vtonError}
        </motion.div>
      )}

      <VirtualMirror
        userImage={userImage}
        productImage={selectedProduct?.image_url}
        resultImage={resultImage}
        loading={loading}
        progress={progress}
        onUserImageUpload={handleImageUpload}
        onGenerate={handleGenerate}
      />

      {history.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-16"
        >
          <div className="flex items-center gap-2 mb-6">
            <svg className="w-5 h-5 text-editorial-gray" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2m0 0v5.586a1 1 0 01-.293.707l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" />
            </svg>
            <h2 className="text-lg font-display font-semibold text-editorial-black">Historial</h2>
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
        </motion.div>
      )}

      <UpgradeModal
        isOpen={showUpgrade}
        onClose={hideUpgradeModal}
        onUpgrade={handleUpgrade}
        loading={upgradeLoading}
        error={upgradeError}
      />
    </div>
  );
};

export default VirtualTryOn;