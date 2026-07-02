import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import api from "../services/api";

function ModalVTON({ product, isOpen, onClose }) {
  const [userImage, setUserImage] = useState(null);
  const [userFile, setUserFile] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      if (file.size > 10 * 1024 * 1024) {
        setError("La imagen no puede superar 10MB.");
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        setUserImage(e.target.result);
        setUserFile(file);
        setResultImage(null);
        setError(null);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg"] },
    maxFiles: 1,
    multiple: false,
    maxSize: 10 * 1024 * 1024,
  });

  const handleGenerate = async () => {
    if (!userFile || !product) return;
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("user_image", userFile);
      formData.append("product_id", product.id);

      const res = await api.post("/vton/try-on", formData);

      if (res.data?.output_image_url) {
        setResultImage(res.data.output_image_url);
      } else {
        setError("No se pudo generar el resultado. Intenta con otra foto.");
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Error al procesar la imagen.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setUserImage(null);
    setUserFile(null);
    setResultImage(null);
    setError(null);
    setLoading(false);
    onClose();
  };

  if (!isOpen || !product) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-bounce-in">
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl z-10">
          <h2 className="font-serif text-xl font-semibold">Virtual Try-On</h2>
          <button
            onClick={handleClose}
            className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex items-center gap-4 bg-gray-50 rounded-xl p-4">
            <div className="w-16 h-16 rounded-xl overflow-hidden bg-gray-200 flex-shrink-0">
              <img
                src={product.image_url || "/placeholder.jpg"}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="min-w-0">
              <p className="font-medium text-gray-900 truncate">{product.name}</p>
              <p className="text-sm text-gray-500">{product.store}</p>
              <p className="text-sm font-semibold text-fashion-pink">
                {product.currency || "$"}{Number(product.price)?.toLocaleString("es-CL")}
              </p>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Tu foto
              </p>
              <div
                {...getRootProps()}
                className={`aspect-[3/4] rounded-xl border-2 border-dashed flex items-center justify-center cursor-pointer transition-all ${
                  isDragActive
                    ? "border-fashion-pink bg-fashion-pink-light"
                    : "border-gray-200 hover:border-fashion-pink bg-gray-50"
                }`}
              >
                <input {...getInputProps()} />
                {userImage ? (
                  <img
                    src={userImage}
                    alt="Tu foto"
                    className="w-full h-full object-cover rounded-xl"
                  />
                ) : (
                  <div className="text-center p-4">
                    <svg
                      className="mx-auto h-8 w-8 text-gray-300"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    <p className="mt-2 text-xs text-gray-400">
                      {isDragActive ? "Suelta tu foto aquí" : "Sube tu foto (máx. 10MB)"}
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Resultado
              </p>
              <div className="aspect-[3/4] rounded-xl bg-gray-50 border border-gray-200 flex items-center justify-center overflow-hidden">
                {loading ? (
                  <div className="text-center">
                    <div className="w-10 h-10 rounded-full border-2 border-fashion-pink/20 border-t-fashion-pink animate-spin mx-auto" />
                    <p className="mt-2 text-xs text-gray-400">Generando...</p>
                  </div>
                ) : resultImage ? (
                  <img
                    src={resultImage}
                    alt="Resultado"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <p className="text-xs text-gray-300">Esperando prueba...</p>
                )}
              </div>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!userImage || loading}
            className="w-full btn-primary py-3 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? "Generando..." : "Probar ahora"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ModalVTON;
