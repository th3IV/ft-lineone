import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

function VirtualMirror({
  userImage,
  productImage,
  resultImage,
  loading,
  canGenerate,
  onUserImageUpload,
  onGenerate,
}) {
  const onDrop = useCallback(
    (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];
        const reader = new FileReader();
        reader.onload = (e) => onUserImageUpload(e.target.result, file);
        reader.readAsDataURL(file);
      }
    },
    [onUserImageUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg"] },
    maxFiles: 1,
    multiple: false,
  });

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-2xl card-shadow p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">Tu Foto</h3>
          <div
            {...getRootProps()}
            className={`aspect-square flex items-center justify-center cursor-pointer rounded-xl border-2 border-dashed transition-all ${
              isDragActive
                ? "border-fashion-pink bg-fashion-pink-light"
                : "border-gray-200 bg-gray-50 hover:border-fashion-pink/50"
            }`}
          >
            <input {...getInputProps()} />
            {userImage ? (
              <img src={userImage} alt="User" className="w-full h-full object-cover rounded-lg" />
            ) : isDragActive ? (
              <p className="text-fashion-pink text-sm text-center px-2 font-medium">Suelta tu foto aquí</p>
            ) : (
              <div className="text-center px-4">
                <svg className="mx-auto h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="mt-2 text-sm text-gray-500">Arrastra o haz clic para subir</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl card-shadow p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">Prenda</h3>
          <div className="aspect-square flex items-center justify-center bg-gray-50 rounded-xl">
            {productImage ? (
              <img src={productImage} alt="Product" className="w-full h-full object-cover rounded-lg" />
            ) : (
              <p className="text-gray-400 text-sm">Sin prenda seleccionada</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl card-shadow p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 text-center">Resultado</h3>
          <div className="aspect-square flex items-center justify-center bg-gray-50 rounded-xl relative">
            {loading ? (
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 rounded-full border-2 border-fashion-pink/20 border-t-fashion-pink animate-spin" />
                <p className="mt-3 text-sm text-gray-500 font-medium">Procesando...</p>
              </div>
            ) : resultImage ? (
              <img src={resultImage} alt="Try-On Result" className="w-full h-full object-cover rounded-lg" />
            ) : (
              <div className="text-center px-4">
                <svg className="mx-auto h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="mt-2 text-sm text-gray-400">Esperando...</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 text-center">
        <button
          onClick={onGenerate}
          disabled={!canGenerate || loading}
          className="btn-primary text-lg px-10 py-3 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center gap-2 justify-center">
              <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
              Generando...
            </span>
          ) : (
            "Generate Try-On"
          )}
        </button>
      </div>
    </div>
  );
}

export default VirtualMirror;
