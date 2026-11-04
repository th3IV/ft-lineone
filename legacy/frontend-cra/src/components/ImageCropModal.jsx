import React, { useState, useCallback } from "react";
import Cropper from "react-easy-crop";
import { getCroppedImg } from "../utils/cropImage";

export default function ImageCropModal({ image, onConfirm, onCancel }) {
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);

  const onCropComplete = useCallback((_, croppedPixels) => {
    setCroppedAreaPixels(croppedPixels);
  }, []);

  const handleConfirm = async () => {
    if (!croppedAreaPixels) return;
    const base64 = await getCroppedImg(image, croppedAreaPixels);
    onConfirm(base64);
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-editorial-black/90 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <p className="text-sm font-medium text-white">Editar foto</p>
        <button
          onClick={onCancel}
          className="w-8 h-8 flex items-center justify-center rounded-full text-white/60 hover:text-white hover:bg-white/10 transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Cropper */}
      <div className="relative flex-1 mx-4 my-2 overflow-hidden rounded-xl">
        <Cropper
          image={image}
          crop={crop}
          zoom={zoom}
          aspect={1}
          onCropChange={setCrop}
          onZoomChange={setZoom}
          onCropComplete={onCropComplete}
          cropShape="round"
          showGrid={false}
        />
      </div>

      {/* Zoom slider */}
      <div className="px-6 py-3">
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-white/40 tracking-wider">ZOOM</span>
          <input
            type="range"
            min={1}
            max={3}
            step={0.1}
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            className="flex-1 h-1 rounded-full appearance-none bg-white/20 accent-white"
          />
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-center gap-4 px-6 pb-6 pt-2">
        <button
          onClick={onCancel}
          className="px-8 py-2.5 text-sm tracking-wide text-white/60 border border-white/20 rounded-full hover:bg-white/5 transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={handleConfirm}
          className="px-8 py-2.5 text-sm tracking-wide text-white bg-editorial-black border border-white/20 rounded-full hover:bg-editorial-black/80 transition-colors"
        >
          Confirmar ✓
        </button>
      </div>
    </div>
  );
}
