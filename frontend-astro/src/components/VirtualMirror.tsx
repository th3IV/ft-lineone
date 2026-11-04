import { useCallback, useRef } from "react";
import { motion } from "framer-motion";

interface VirtualMirrorProps {
  userImage: string | null;
  productImage?: string;
  resultImage: string | null;
  loading: boolean;
  progress: number;
  onUserImageUpload: (file: File) => void;
  onGenerate: () => void;
}

export const VirtualMirror = ({
  userImage,
  productImage,
  resultImage,
  loading,
  progress,
  onUserImageUpload,
  onGenerate,
}: VirtualMirrorProps) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUserImageUpload(file);
    },
    [onUserImageUpload]
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* User Image */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="relative"
      >
        <label className="editorial-label block mb-3">Tu foto</label>
        <div
          className="aspect-[3/4] rounded-2xl border-2 border-dashed border-editorial-cream-dark bg-editorial-white flex items-center justify-center overflow-hidden cursor-pointer hover:border-editorial-gold transition-colors"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); }}
          onDrop={(e) => {
            e.preventDefault();
            const file = e.dataTransfer.files[0];
            if (file) onUserImageUpload(file);
          }}
        >
          {userImage ? (
            <img src={userImage} alt="Tu foto" className="w-full h-full object-cover" />
          ) : (
            <div className="text-center p-6">
              <svg className="w-12 h-12 mx-auto text-editorial-gray mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-sm text-editorial-gray">Arrastra o haz click para subir</p>
            </div>
          )}
        </div>
        <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
      </motion.div>

      {/* Product Image */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <label className="editorial-label block mb-3">Prenda seleccionada</label>
        <div className="aspect-[3/4] rounded-2xl bg-editorial-cream-dark flex items-center justify-center overflow-hidden">
          {productImage ? (
            <img src={productImage} alt="Prenda" className="w-full h-full object-cover" />
          ) : (
            <div className="text-center p-6">
              <svg className="w-12 h-12 mx-auto text-editorial-gray mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
              </svg>
              <p className="text-sm text-editorial-gray">Selecciona una prenda</p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Result */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
      >
        <label className="editorial-label block mb-3">Resultado</label>
        <div className="aspect-[3/4] rounded-2xl bg-editorial-cream-dark flex items-center justify-center overflow-hidden">
          {loading ? (
            <div className="text-center p-6">
              <div className="loader mb-4 mx-auto" />
              <p className="text-sm text-editorial-gray">Generando...</p>
              {progress > 0 && (
                <div className="w-32 h-1.5 bg-editorial-cream-dark rounded-full mt-3 mx-auto overflow-hidden">
                  <div
                    className="h-full bg-editorial-gold rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              )}
            </div>
          ) : resultImage ? (
            <img src={resultImage} alt="Resultado" className="w-full h-full object-cover" />
          ) : (
            <div className="text-center p-6">
              <svg className="w-12 h-12 mx-auto text-editorial-gray mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <p className="text-sm text-editorial-gray">El resultado aparecera aqui</p>
            </div>
          )}
        </div>
        {userImage && productImage && !loading && !resultImage && (
          <button
            onClick={onGenerate}
            className="w-full mt-4 btn-primary py-3"
          >
            Generar prueba virtual
          </button>
        )}
        {resultImage && (
          <div className="flex gap-2 mt-4">
            <a
              href={resultImage}
              download
              className="flex-1 btn-secondary py-2 text-center text-sm"
            >
              Descargar
            </a>
            <button
              onClick={onGenerate}
              className="flex-1 btn-secondary py-2 text-sm"
            >
              Regenerar
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
};
