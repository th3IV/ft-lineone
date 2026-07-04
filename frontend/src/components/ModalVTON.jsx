import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { X, Upload, Sparkles, Loader2, AlertCircle } from "lucide-react";
import { compressImage } from "../utils/compressImage";
import { useVtonPolling } from "../hooks/useVtonPolling";

const PHOTO_TIPS = [
  "Foto de cuerpo completo, de frente",
  "Buena iluminacion, fondo claro",
  "Maximo 10MB — se comprimira automaticamente",
];

function ModalVTON({ product, isOpen, onClose }) {
  const [userImage, setUserImage] = useState(null);
  const { loading, error, resultImage, progress, generate, reset } =
    useVtonPolling();

  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        try {
          const { dataUrl } = await compressImage(file);
          setUserImage(dataUrl);
          reset();
        } catch {
          // error handled by parent
        }
      }
    },
    [reset]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg"] },
    maxFiles: 1,
    multiple: false,
    maxSize: 10 * 1024 * 1024,
  });

  const handleGenerate = async () => {
    if (!userImage || !product) return;
    await generate(product.id, userImage, product.image_url);
  };

  const handleClose = () => {
    setUserImage(null);
    reset();
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && product && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={handleClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="relative bg-white w-full max-w-2xl max-h-[90vh] overflow-y-auto"
          >
            <div className="sticky top-0 bg-white/90 backdrop-blur-sm border-b border-editorial-gray-light px-6 py-4 flex items-center justify-between z-10">
              <h2 className="font-display text-lg font-semibold tracking-tight">
                Virtual Try-On
              </h2>
              <button
                onClick={handleClose}
                className="p-2 text-editorial-gray hover:text-editorial-black transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-sm overflow-hidden bg-editorial-gray-light flex-shrink-0">
                  <img
                    src={product.image_url || "/placeholder.jpg"}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-editorial-black truncate">
                    {product.name}
                  </p>
                  <p className="text-xs text-editorial-gray-light">
                    {product.store}
                  </p>
                  <p className="text-sm font-semibold font-mono text-editorial-black mt-0.5">
                    {product.currency || "$"}
                    {Number(product.price)?.toLocaleString("es-CL")}
                  </p>
                </div>
              </div>

              {error && (
                <div className="flex items-start gap-2 text-sm text-red-500 bg-red-50 p-3">
                  <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {loading && progress.elapsed > 0 && (
                <div className="text-xs text-editorial-gray text-center">
                  Generando... ({progress.elapsed}s)
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="editorial-label">Tu foto</p>
                  <div
                    {...getRootProps()}
                    className={`aspect-[3/4] border border-dashed flex items-center justify-center cursor-pointer transition-all ${
                      isDragActive
                        ? "border-editorial-black bg-editorial-cream"
                        : "border-editorial-gray-light hover:border-editorial-black bg-editorial-cream-light"
                    }`}
                  >
                    <input {...getInputProps()} />
                    {userImage ? (
                      <img
                        src={userImage}
                        alt="Tu foto"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="text-center p-4">
                        <Upload
                          size={24}
                          className="mx-auto text-editorial-gray-light mb-2"
                        />
                        <p className="text-xs text-editorial-gray">
                          {isDragActive
                            ? "Suelta tu foto aqui"
                            : "Sube tu foto (max. 10MB)"}
                        </p>
                      </div>
                    )}
                  </div>
                  {!userImage && (
                    <ul className="mt-1.5 space-y-0.5">
                      {PHOTO_TIPS.map((tip) => (
                        <li
                          key={tip}
                          className="text-[10px] text-editorial-gray-light flex items-start gap-1"
                        >
                          <span className="text-editorial-gray mt-px">·</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div>
                  <p className="editorial-label">Resultado</p>
                  <div className="aspect-[3/4] bg-editorial-cream-light border border-editorial-gray-light flex items-center justify-center overflow-hidden">
                    {loading ? (
                      <div className="text-center">
                        <Loader2
                          size={28}
                          className="mx-auto text-editorial-gray-light animate-spin mb-2"
                        />
                        <p className="text-xs text-editorial-gray">
                          Generando...
                        </p>
                      </div>
                    ) : resultImage ? (
                      <img
                        src={resultImage}
                        alt="Resultado"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <p className="text-xs text-editorial-gray-light">
                        Esperando prueba...
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <button
                onClick={handleGenerate}
                disabled={!userImage || loading}
                className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Generando...
                  </>
                ) : (
                  <>
                    <Sparkles size={14} />
                    Probar ahora
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default ModalVTON;
