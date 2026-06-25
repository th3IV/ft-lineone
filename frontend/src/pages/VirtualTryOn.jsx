import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import toast from "react-hot-toast";
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
    if (!userFile || !selectedProductId) {
      toast.error("Selecciona un producto y sube una foto primero.");
      return;
    }
    setLoading(true);
    const toastId = toast.loading("Generando try-on...");
    try {
      const formData = new FormData();
      formData.append("user_image", userFile);
      formData.append("product_id", selectedProductId);
      const result = await requestTryOn(formData);
      setResultImage(result.image_url);
      const entry = {
        id: Date.now(),
        productId: selectedProductId,
        productName: selectedProduct?.name,
        resultImage: result.image_url,
        timestamp: new Date().toISOString(),
      };
      const updated = [entry, ...history].slice(0, 10);
      setHistory(updated);
      localStorage.setItem("tryOnHistory", JSON.stringify(updated));
      toast.success("Try-on generado exitosamente!", { id: toastId });
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Error al generar try-on";
      toast.error(msg, { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  const loadFromHistory = (entry) => {
    setSelectedProductId(String(entry.productId));
    setResultImage(entry.resultImage);
  };

  const canGenerate = !!userFile && !!selectedProductId;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-fashion-pink to-fashion-purple bg-clip-text text-transparent">
          Virtual Try-On
        </h1>
        <p className="text-gray-500 mt-2">Sube tu foto y pruebate la prenda virtualmente</p>
      </div>

      <div className="bg-white rounded-2xl card-shadow p-6 mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">Selecciona una prenda</label>
        <select
          value={selectedProductId}
          onChange={(e) => {
            setSelectedProductId(e.target.value);
            setResultImage(null);
          }}
          className="w-full max-w-md border border-gray-200 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent bg-white"
        >
          <option value="">Elige un producto...</option>
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
        canGenerate={canGenerate}
        onUserImageUpload={handleUserImageUpload}
        onGenerate={handleGenerate}
      />

      {history.length > 0 && (
        <section className="mt-12">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Historial de Try-On</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
            {history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => loadFromHistory(entry)}
                className="aspect-square rounded-xl overflow-hidden bg-gray-100 border-2 border-transparent hover:border-fashion-pink transition-all hover:shadow-lg"
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
