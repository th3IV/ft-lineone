import { useCallback, useState, useEffect, useRef } from "react";
import { useDropzone } from "react-dropzone";
import { Camera, Upload, Sparkles, AlertCircle, RefreshCw, X } from "lucide-react";
import { compressImage } from "../utils/compressImage";

const PHOTO_TIPS = [
  "Foto de cuerpo completo, de frente",
  "Buena iluminacion, fondo claro",
  "Maximo 10MB — se comprimira automaticamente",
];

const LOADING_TIMEOUT = 120000;

function VirtualMirror({
  userImage,
  productImage,
  resultImage,
  loading,
  onUserImageUpload,
  onGenerate,
}) {
  const [error, setError] = useState(null);
  const [loadingTime, setLoadingTime] = useState(0);
  const [cameraActive, setCameraActive] = useState(false);
  const [facingMode, setFacingMode] = useState("user");
  const timerRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    if (loading) {
      setLoadingTime(0);
      timerRef.current = setInterval(() => {
        setLoadingTime((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
      setLoadingTime(0);
    }
    return () => clearInterval(timerRef.current);
  }, [loading]);

  const onDrop = useCallback(
    async (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        setError(null);
        try {
          const { dataUrl } = await compressImage(file);
          onUserImageUpload(dataUrl, file);
        } catch {
          setError("No se pudo procesar la imagen. Intenta con otra foto.");
        }
      }
    },
    [onUserImageUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg"] },
    maxFiles: 1,
    multiple: false,
    maxSize: 10 * 1024 * 1024,
  });

  const isTimeout = loading && loadingTime >= LOADING_TIMEOUT / 1000;

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 768 }, height: { ideal: 1024 } },
      });
      streamRef.current = stream;
      setCameraActive(true);
    } catch (err) {
      console.error("Error accessing camera:", err);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

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
            onUserImageUpload(dataUrl, file);
          } catch {
            setError("No se pudo procesar la imagen.");
          }
        }
        stopCamera();
      },
      "image/jpeg",
      0.8
    );
  };

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

  useEffect(() => {
    if (cameraActive && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(() => {});
    }
  }, [cameraActive]);

  useEffect(() => {
    return () => stopCamera();
  }, []);

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border border-editorial-black/10 rounded-2xl p-4">
          <h3 className="editorial-label text-center mb-3">Tu Foto</h3>
          {cameraActive ? (
            <div className="aspect-[3/4] relative bg-black rounded-xl overflow-hidden">
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
                  className="w-14 h-14 rounded-full bg-white border-4 border-editorial-black/20 flex items-center justify-center hover:scale-105 transition-transform"
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
                className={`aspect-[3/4] flex items-center justify-center cursor-pointer rounded-xl transition-colors ${
                  isDragActive
                    ? "bg-editorial-cream border-editorial-black"
                    : "bg-editorial-cream-dark"
                }`}
              >
                <input {...getInputProps()} />
                {userImage ? (
                  <img
                    src={userImage}
                    alt="User"
                    className="w-full h-full object-cover rounded-xl"
                  />
                ) : isDragActive ? (
                  <p className="text-editorial-gray text-sm text-center px-2">
                    Suelta tu foto aqui
                  </p>
                ) : (
                  <div className="text-center px-4">
                    <Upload
                      size={32}
                      className="mx-auto text-editorial-gray-light mb-2"
                    />
                    <p className="text-xs text-editorial-gray">
                      Arrastra o haz click para subir
                    </p>
                  </div>
                )}
              </div>
          {!userImage && !cameraActive && (
                <button
                  onClick={startCamera}
                  className="mt-2 w-full flex items-center justify-center gap-2 py-2 px-4 border border-editorial-black/20 text-editorial-black text-xs font-medium hover:bg-editorial-cream transition-colors rounded-lg"
                >
                  <Camera size={14} />
                  Usar camara
                </button>
              )}
            </>
          )}
          {!userImage && (
            <ul className="mt-2 space-y-0.5">
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
          {error && (
            <div className="mt-2 flex items-start gap-1.5 text-[11px] text-red-500">
              <AlertCircle size={12} className="mt-px flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className="border border-editorial-black/10 rounded-2xl p-4">
          <h3 className="editorial-label text-center mb-3">Prenda</h3>
          <div className="aspect-[3/4] flex items-center justify-center bg-editorial-cream-dark rounded-xl">
            {productImage ? (
              <img
                src={productImage}
                alt="Product"
                className="w-full h-full object-cover rounded-xl"
              />
            ) : (
              <p className="text-editorial-gray-light text-xs">
                Selecciona una prenda arriba
              </p>
            )}
          </div>
        </div>

        <div className="border border-editorial-black/10 rounded-2xl p-4">
          <h3 className="editorial-label text-center mb-3">Resultado</h3>
          <div className="aspect-[3/4] flex items-center justify-center bg-editorial-cream-dark rounded-xl relative">
            {loading ? (
              <div className="flex flex-col items-center">
                {isTimeout ? (
                  <>
                    <AlertCircle
                      size={28}
                      className="text-editorial-gray mb-2"
                    />
                    <p className="text-xs text-editorial-gray text-center px-2">
                      El proceso esta tomando mucho tiempo.
                      <br />
                      Intenta mas tarde.
                    </p>
                  </>
                ) : (
                  <>
                    <div className="w-8 h-8 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
                    <p className="mt-2 text-xs text-editorial-gray">
                      Procesando... ({loadingTime}s)
                    </p>
                  </>
                )}
              </div>
            ) : resultImage ? (
              <img
                src={resultImage}
                alt="Try-On Result"
                className="w-full h-full object-cover rounded-xl"
              />
            ) : (
              <p className="text-editorial-gray-light text-xs">
                Sube tu foto y selecciona una prenda
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 text-center">
        <button
          onClick={onGenerate}
          disabled={!userImage || !productImage || loading || isTimeout}
          className="btn-primary inline-flex items-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Sparkles size={16} />
          {loading ? "Generando..." : "Generar Try-On"}
        </button>
      </div>
    </div>
  );
}

export default VirtualMirror;
