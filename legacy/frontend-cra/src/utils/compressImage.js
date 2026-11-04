/**
 * Compress an image file to fit within maxBytes.
 * Uses canvas to resize and re-encode as JPEG with progressive quality.
 *
 * @param {File} file - The original image file
 * @param {number} maxBytes - Max output size in bytes (default 100KB)
 * @param {number} maxWidth - Max width in pixels (default 768)
 * @returns {Promise<{ file: File, dataUrl: string }>} Compressed file and data URL
 */
export async function compressImage(file, maxBytes = 100 * 1024, maxWidth = 768) {
  const img = await loadImage(file);
  const { width, height } = fitDimensions(img.width, img.height, maxWidth);

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, width, height);

  let quality = 0.85;
  let blob = await canvasToBlob(canvas, "image/jpeg", quality);

  while (blob.size > maxBytes && quality > 0.1) {
    quality -= 0.1;
    blob = await canvasToBlob(canvas, "image/jpeg", quality);
  }

  if (blob.size > maxBytes) {
    const scale = Math.sqrt(maxBytes / blob.size);
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    quality = 0.7;
    blob = await canvasToBlob(canvas, "image/jpeg", quality);
  }

  const compressedFile = new File([blob], file.name.replace(/\.[^.]+$/, ".jpg"), {
    type: "image/jpeg",
    lastModified: Date.now(),
  });

  const dataUrl = await fileToDataUrl(compressedFile);

  return { file: compressedFile, dataUrl };
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(img.src);
      resolve(img);
    };
    img.onerror = () => reject(new Error("No se pudo cargar la imagen"));
    img.src = URL.createObjectURL(file);
  });
}

function fitDimensions(w, h, maxW) {
  if (w <= maxW) return { width: w, height: h };
  const ratio = maxW / w;
  return { width: maxW, height: Math.round(h * ratio) };
}

function canvasToBlob(canvas, type, quality) {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), type, quality);
  });
}

function fileToDataUrl(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.readAsDataURL(file);
  });
}
