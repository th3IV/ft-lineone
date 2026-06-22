import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { fetchProducts, fetchProductById } from "../store/productSlice";
import { requestTryOn } from "../services/vton";
import { useDropzone } from "react-dropzone";

function VirtualTryOn() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { products, selectedProduct } = useSelector((state) => state.products);

  const [selectedProductId, setSelectedProductId] = useState(searchParams.get("product") || "");
  const [userImage, setUserImage] = useState(null);
  const [userFile, setUserFile] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(searchParams.get("product") ? "upload" : "select");
  const [history, setHistory] = useState([]);

  useEffect(() => {
    dispatch(fetchProducts({ limit: 50 }));
    if (searchParams.get("product")) {
      dispatch(fetchProductById(searchParams.get("product")));
    }
    const saved = localStorage.getItem("tryOnHistory");
    if (saved) {
      try { setHistory(JSON.parse(saved)); } catch {}
    }
  }, [dispatch, searchParams]);

  const product = selectedProductId
    ? selectedProduct
      ? selectedProduct
      : products.find((p) => String(p.id) === selectedProductId)
    : null;

  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        const reader = new FileReader();
        reader.onload = (e) => {
          setUserImage(e.target.result);
          setUserFile(file);
          setResultImage(null);
        };
        reader.readAsDataURL(file);
      }
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg"] },
    maxFiles: 1,
    multiple: false,
  });

  const handleProductChange = (e) => {
    const val = e.target.value;
    setSelectedProductId(val);
    setResultImage(null);
    if (val) {
      dispatch(fetchProductById(val));
      setStep("upload");
    } else {
      setStep("select");
    }
  };

  const handleGenerate = async () => {
    if (!userFile || !selectedProductId) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("user_image", userFile);
      formData.append("product_id", selectedProductId);
      const result = await requestTryOn(formData);
      setResultImage(result.image_url);
      setStep("result");

      const entry = {
        id: Date.now(),
        productId: selectedProductId,
        productName: product?.name,
        resultImage: result.image_url,
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
    dispatch(fetchProductById(entry.productId));
    setResultImage(entry.resultImage);
    setStep("result");
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <nav className="text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-indigo-600">Inicio</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">Probador Virtual</span>
      </nav>

      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Probador Virtual</h1>
        <p className="text-gray-500 mt-2">
          Sube tu foto y mira cómo te queda la prenda antes de comprar
        </p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Selecciona una prenda
        </label>
        <select
          value={selectedProductId}
          onChange={handleProductChange}
          className="w-full max-w-md border border-gray-300 rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        >
          <option value="">Elige un producto...</option>
          {products.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} - ${p.price?.toFixed(0)} ({p.store})
            </option>
          ))}
        </select>
      </div>

      {product && (
        <div className="flex items-center gap-4 bg-gray-50 rounded-xl p-4 mb-6">
          <div className="w-16 h-16 rounded-lg bg-gray-200 overflow-hidden flex-shrink-0">
            <img src={product.image_url || "/placeholder.jpg"} alt={product.name} className="w-full h-full object-cover" />
          </div>
          <div>
            <p className="font-medium text-gray-900">{product.name}</p>
            <p className="text-sm text-gray-500">{product.store} - ${product.price?.toFixed(0)}</p>
          </div>
          <Link
            to={`/product/${product.id}`}
            className="ml-auto text-sm text-indigo-600 hover:text-indigo-800 font-medium"
          >
            Ver detalle →
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div>
          <div className="text-center mb-3">
            <h3 className="text-lg font-semibold text-gray-900">1. Tu foto</h3>
            <p className="text-sm text-gray-500">
              Foto de cuerpo completo, buena iluminación, sin accesorios
            </p>
          </div>
          <div
            {...getRootProps()}
            className={`aspect-[3/4] flex items-center justify-center cursor-pointer rounded-xl border-2 border-dashed transition-colors ${
              isDragActive
                ? "bg-indigo-50 border-indigo-400"
                : userImage
                  ? "bg-gray-50 border-green-400"
                  : "bg-gray-50 border-gray-300 hover:border-indigo-400"
            }`}
          >
            <input {...getInputProps()} />
            {userImage ? (
              <img src={userImage} alt="User" className="w-full h-full object-cover rounded-xl" />
            ) : isDragActive ? (
              <div className="text-center px-4">
                <p className="text-indigo-600 font-medium">Suelta tu foto aquí</p>
              </div>
            ) : (
              <div className="text-center px-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-200 flex items-center justify-center">
                  <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-sm text-gray-500 mb-1">Arrastra o haz clic para subir tu foto</p>
                <p className="text-xs text-gray-400">PNG, JPG. Cuerpo completo, ropa ajustada</p>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="text-center mb-3">
            <h3 className="text-lg font-semibold text-gray-900">2. Resultado</h3>
            <p className="text-sm text-gray-500">
              {step === "result" ? "Así se verá la prenda en ti" : "La IA generará la imagen aquí"}
            </p>
          </div>
          <div className="aspect-[3/4] bg-gray-50 rounded-xl border-2 border-gray-200 flex items-center justify-center relative overflow-hidden">
            {loading ? (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                <p className="mt-4 text-sm text-gray-500">Generando tu look...</p>
                <p className="text-xs text-gray-400 mt-1">Puede tardar hasta 2 minutos</p>
              </div>
            ) : resultImage ? (
              <img src={resultImage} alt="Try-On Result" className="w-full h-full object-cover" />
            ) : (
              <div className="text-center px-8">
                <svg className="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
                </svg>
                <p className="text-gray-400 font-medium">Esperando...</p>
                <p className="text-xs text-gray-300 mt-1">Selecciona producto y sube tu foto</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="text-center">
        <button
          onClick={handleGenerate}
          disabled={!userFile || !selectedProductId || loading}
          className="bg-indigo-600 text-white px-10 py-3 rounded-xl text-lg font-semibold hover:bg-indigo-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed inline-flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              Generando...
            </>
          ) : (
            <>
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
              </svg>
              Generar Probador
            </>
          )}
        </button>
      </div>

      {history.length > 0 && (
        <section className="mt-16">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Historial de Probadores</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
            {history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => loadFromHistory(entry)}
                className="aspect-square rounded-lg overflow-hidden bg-gray-100 border-2 border-transparent hover:border-indigo-600 transition-all hover:shadow-lg"
              >
                <img src={entry.resultImage} alt={entry.productName} className="w-full h-full object-cover" />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                  <p className="text-white text-xs truncate">{entry.productName}</p>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default VirtualTryOn;
