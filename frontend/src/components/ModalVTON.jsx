import { useState, useCallback, useRef, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { X, Upload, Sparkles, Loader2, AlertCircle, Camera, RefreshCw, Crown, Zap } from "lucide-react";
import { useSelector } from "react-redux";
import { compressImage } from "../utils/compressImage";
import { useVtonPolling } from "../hooks/useVtonPolling";
import { useFeatureGate } from "../hooks/useFeatureGate";
import UpgradeModal from "./UpgradeModal";
import RemainingUses from "./RemainingUses";
import HypnoticLoader from "./HypnoticLoader";

const PHOTO_TIPS = [
  "Foto de cuerpo completo, de frente",
  "Buena iluminacion, fondo claro",
  "Maximo 10MB — se comprimira automaticamente",
];

function ModalVTON({ product, isOpen, onClose }) {
  const [userImage, setUserImage] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [facingMode, setFacingMode] = useState("user");
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const { isAuthenticated } = useSelector((state) => state.user);
  const { loading, error, resultImage, progress, generate, reset } =
    useVtonPolling();
  const {
    isPremium,
    vtonUsed,
    vtonRemaining,
    canUseVton,
    getUsageColor,
    showUpgrade,
    showUpgradeModal,
    hideUpgradeModal,
    handleUpgrade,
    limits,
  } = useFeatureGate();

  const isLimitReached = !canUseVton;

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

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facingMode, width: { ideal: 768 }, height: { ideal: 1024 } },
      });
      streamRef.current = stream;
      setCameraActive(true);
    } catch (err) {
      console.error("Error accessing camera:", err);
    }
  };

  // Attach stream to video element after it renders
  useEffect(() => {
    if (cameraActive && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(() => {});
    }
  }, [cameraActive]);

  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  // Capture photo from camera
  const capturePhoto = async () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    if (facingMode === "user") {
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(videoRef.current, 0, 0);

    canvas.toBlob(
      async (blob) => {
        if (blob) {
          const file = new File([blob], "camera-photo.jpg", { type: "image/jpeg" });
          try {
            const { dataUrl } = await compressImage(file);
            setUserImage(dataUrl);
            reset();
          } catch {
            // error handled by parent
          }
        }
        stopCamera();
      },
      "image/jpeg",
      0.8
    );
  };

  // Switch between front and back camera
  const switchCamera = async () => {
    stopCamera();
    const newFacing = facingMode === "user" ? "environment" : "user";
    setFacingMode(newFacing);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: newFacing, width: { ideal: 768 }, height: { ideal: 1024 } },
      });
      streamRef.current = stream;
      setCameraActive(true);
    } catch (err) {
      console.error("Error switching camera:", err);
    }
  };

  // Clean up camera on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const handleGenerate = async () => {
    if (!userImage || !product) return;
    if (!isAuthenticated) {
      window.location.href = "/login";
      return;
    }
    if (isLimitReached) {
      showUpgradeModal();
      return;
    }
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
                  {cameraActive ? (
                    <div className="aspect-[3/4] relative bg-black">
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-full object-cover"
                        style={{ transform: facingMode === "user" ? "scaleX(-1)" : "none" }}
                      />
                      <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-3">
                        <button
                          onClick={capturePhoto}
                          className="w-14 h-14 rounded-full bg-white border-4 border-editorial-black flex items-center justify-center hover:bg-gray-100 transition-colors"
                        >
                          <Camera size={24} className="text-editorial-black" />
                        </button>
                        <button
                          onClick={switchCamera}
                          className="w-10 h-10 rounded-full bg-black/50 flex items-center justify-center text-white hover:bg-black/70 transition-colors"
                          title="Cambiar camara"
                        >
                          <RefreshCw size={18} />
                        </button>
                        <button
                          onClick={stopCamera}
                          className="w-10 h-10 rounded-full bg-black/50 flex items-center justify-center text-white hover:bg-black/70 transition-colors"
                        >
                          <X size={18} />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
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
                          <div className="relative w-full h-full">
                            <img
                              src={userImage}
                              alt="Tu foto"
                              className="w-full h-full object-cover"
                            />
                            <button
                              onClick={(e) => { e.stopPropagation(); setUserImage(null); reset(); }}
                              className="absolute top-2 left-2 w-7 h-7 rounded-full bg-black/60 text-white flex items-center justify-center hover:bg-black/80 transition-colors z-10"
                              title="Eliminar foto"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <div className="text-center p-4">
                            <Upload
                              size={24}
                              className="mx-auto text-editorial-gray-light mb-2"
                            />
                            <p className="text-xs text-editorial-gray">
                              Ingresar imagen o sacar foto
                            </p>
                          </div>
                        )}
                      </div>
                      {!userImage && (
                        <button
                          onClick={startCamera}
                          className="mt-2 w-full flex items-center justify-center gap-2 py-2 px-4 border border-editorial-black/20 text-editorial-black text-xs font-medium hover:bg-editorial-cream transition-colors"
                        >
                          <Camera size={14} />
                          Usar camara
                        </button>
                      )}
                    </>
                  )}
                  {!userImage && !cameraActive && (
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
                      <HypnoticLoader variant="generating" />
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

              {/* Remaining uses for free users */}
              {!isPremium && (
                <RemainingUses
                  type="vton"
                  used={vtonUsed}
                  limit={limits.vton}
                  color={getUsageColor(vtonUsed)}
                />
              )}

              {/* Usage limit block */}
              {isLimitReached && (
                <div className="bg-editorial-cream/80 rounded-xl p-4 border border-editorial-gray-light">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                      <Crown size={18} className="text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-editorial-black">Límite diario alcanzado</p>
                      <p className="text-xs text-editorial-gray">Has usado tus 10 pruebas de vestir de hoy</p>
                    </div>
                  </div>
                  <button
                    onClick={showUpgradeModal}
                    className="w-full py-2.5 px-4 bg-editorial-black text-white rounded-xl text-sm font-medium hover:bg-editorial-black/90 transition-all flex items-center justify-center gap-2"
                  >
                    <Zap size={14} />
                    Upgrade a Premium — $4.990/mes
                  </button>
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={!userImage || loading || isLimitReached}
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
          <UpgradeModal
            isOpen={showUpgrade}
            onClose={hideUpgradeModal}
            onUpgrade={handleUpgrade}
          />
        </div>
      )}
    </AnimatePresence>
  );
}

export default ModalVTON;
