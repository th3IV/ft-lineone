import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Camera, Upload, Sparkles, AlertCircle } from "lucide-react";
import { compressImage } from "../utils/compressImage";

const PHOTO_TIPS = [
  "Foto de cuerpo completo, de frente",
  "Buena iluminacion, fondo claro",
  "Maximo 10MB — se comprimira automaticamente",
];

function VirtualMirror({
  userImage,
  productImage,
  resultImage,
  loading,
  onUserImageUpload,
  onGenerate,
}) {
  const [error, setError] = useState(null);

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

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* User Photo */}
        <div className="border border-editorial-black/10 rounded-2xl p-4">
          <h3 className="editorial-label text-center mb-3">Tu Foto</h3>
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
                <Camera
                  size={32}
                  className="mx-auto text-editorial-gray-light mb-2"
                />
                <p className="text-xs text-editorial-gray">
                  Arrastra o haz click para subir
                </p>
              </div>
            )}
          </div>
          {!userImage && (
            <ul className="mt-2 space-y-0.5">
              {PHOTO_TIPS.map((tip) => (
                <li key={tip} className="text-[10px] text-editorial-gray-light flex items-start gap-1">
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

        {/* Product */}
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
                Sin prenda seleccionada
              </p>
            )}
          </div>
        </div>

        {/* Result */}
        <div className="border border-editorial-black/10 rounded-2xl p-4">
          <h3 className="editorial-label text-center mb-3">Resultado</h3>
          <div className="aspect-[3/4] flex items-center justify-center bg-editorial-cream-dark rounded-xl relative">
            {loading ? (
              <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
                <p className="mt-2 text-xs text-editorial-gray">
                  Procesando...
                </p>
              </div>
            ) : resultImage ? (
              <img
                src={resultImage}
                alt="Try-On Result"
                className="w-full h-full object-cover rounded-xl"
              />
            ) : (
              <p className="text-editorial-gray-light text-xs">Esperando...</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 text-center">
        <button
          onClick={onGenerate}
          disabled={!userImage || !productImage || loading}
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
