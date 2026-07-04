import { useState, useRef, useCallback, useEffect } from "react";
import { uploadImage, prefetchImage, requestTryOn, pollResult } from "../services/vton";

export function useVtonPolling() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [progress, setProgress] = useState({ attempt: 0, elapsed: 0 });
  const cancelledRef = useRef(false);

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
    };
  }, []);

  const generate = useCallback(async (productId, userImage) => {
    if (!productId || !userImage) return;

    setLoading(true);
    setError(null);
    setResultImage(null);
    setProgress({ attempt: 0, elapsed: 0 });
    cancelledRef.current = false;

    // Step 1: Get data URL for storage + upload to freeimage.host in parallel
    let uploadRes;
    try {
      uploadRes = await uploadImage(userImage);
    } catch (err) {
      if (cancelledRef.current) return null;
      console.error("[VTON] Upload failed:", err);
      const detail = err.response?.data?.detail;
      setError(detail || "No se pudo subir la imagen. Intenta con otra foto.");
      setLoading(false);
      return null;
    }

    if (cancelledRef.current) return null;
    if (!uploadRes.image_url) {
      setError("No se pudo subir la imagen. Intenta con otra foto.");
      setLoading(false);
      return null;
    }

    // Step 2: Pre-upload to freeimage.host (YouCam can't access Worker URLs)
    let prefetchRes;
    try {
      prefetchRes = await prefetchImage(userImage);
    } catch (err) {
      if (cancelledRef.current) return null;
      console.error("[VTON] Prefetch failed:", err);
      // Continue without pre-fetch — /try-on will upload anyway (slower path)
      prefetchRes = null;
    }

    if (cancelledRef.current) return null;

    const publicUrl = prefetchRes?.public_url || undefined;

    // Step 3: Create YouCam task (with pre-uploaded URL if available)
    let tryOnRes;
    try {
      tryOnRes = await requestTryOn(productId, uploadRes.image_url, publicUrl);
    } catch (err) {
      if (cancelledRef.current) return null;
      console.error("[VTON] Try-on request failed:", {
        status: err.response?.status,
        detail: err.response?.data?.detail,
        url: err.config?.url,
        message: err.message,
      });
      const detail = err.response?.data?.detail;
      if (detail) {
        setError(detail);
      } else if (err.response?.status === 500) {
        setError("Error del servidor. Intenta de nuevo mas tarde.");
      } else if (err.code === "ERR_NETWORK") {
        setError("Error de conexion. Verifica tu internet.");
      } else {
        setError(err.message || "Error al procesar el try-on.");
      }
      setLoading(false);
      return null;
    }

    if (cancelledRef.current) return null;

    const vtonId = tryOnRes.id || tryOnRes.vton_id || tryOnRes.request_id;

    if (vtonId) {
      let finalResult;
      try {
        finalResult = await pollResult(vtonId, (p) => {
          if (!cancelledRef.current) {
            setProgress(p);
          }
        });
      } catch (err) {
        if (cancelledRef.current) return null;
        console.error("[VTON] Polling failed:", err);
        setError(err.message || "Error al esperar el resultado.");
        setLoading(false);
        return null;
      }

      if (cancelledRef.current) return null;

      const imageUrl = finalResult.output_image_url || finalResult.image_url;
      if (!imageUrl) {
        setError("No se pudo generar el resultado. Intenta con otra foto.");
        setLoading(false);
        return null;
      }
      setResultImage(imageUrl);
      setLoading(false);
      return imageUrl;
    } else {
      const imageUrl = tryOnRes.output_image_url || tryOnRes.image_url;
      if (!imageUrl) {
        setError("No se pudo generar el resultado. Intenta con otra foto.");
        setLoading(false);
        return null;
      }
      setResultImage(imageUrl);
      setLoading(false);
      return imageUrl;
    }
  }, []);

  const reset = useCallback(() => {
    cancelledRef.current = true;
    setLoading(false);
    setError(null);
    setResultImage(null);
    setProgress({ attempt: 0, elapsed: 0 });
  }, []);

  return { loading, error, resultImage, progress, generate, reset, setError };
}
