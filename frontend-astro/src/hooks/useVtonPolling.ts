import { useState, useCallback, useRef, useEffect } from "react";
import { startVton, getVtonStatus, type VtonStartResponse } from "@/lib/vton";

interface UseVtonPollingReturn {
  loading: boolean;
  error: string | null;
  resultImage: string | null;
  progress: number;
  generate: (productId: string, userImage: string, garmentUrl?: string) => Promise<string | null>;
  reset: () => void;
  setError: (err: string | null) => void;
}

export function useVtonPolling(): UseVtonPollingReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setResultImage(null);
    setProgress(0);
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const pollStatus = useCallback(
    (jobId: string): Promise<string | null> => {
      return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 60; // 5 minutes max (5s intervals)

        pollingRef.current = setInterval(async () => {
          attempts++;
          setProgress(Math.min(90, (attempts / maxAttempts) * 90));

          try {
            const status = await getVtonStatus(jobId);

            if (status.status === "completed") {
              if (pollingRef.current) clearInterval(pollingRef.current);
              setProgress(100);
              setResultImage(status.output_image_url || null);
              resolve(status.output_image_url || null);
            } else if (status.status === "failed") {
              if (pollingRef.current) clearInterval(pollingRef.current);
              setError(status.error || "Error al generar la prueba virtual");
              reject(new Error(status.error || "VTON failed"));
            } else if (attempts >= maxAttempts) {
              if (pollingRef.current) clearInterval(pollingRef.current);
              setError("Tiempo de espera agotado");
              reject(new Error("Timeout"));
            }
          } catch (err: any) {
            if (attempts >= maxAttempts) {
              if (pollingRef.current) clearInterval(pollingRef.current);
              setError(err.message || "Error al consultar estado");
              reject(err);
            }
          }
        }, 5000);
      });
    },
    []
  );

  const generate = useCallback(
    async (productId: string, userImage: string, garmentUrl?: string): Promise<string | null> => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      setLoading(true);
      setError(null);
      setResultImage(null);
      setProgress(10);

      try {
        const response: VtonStartResponse = await startVton({
          product_id: productId,
          image: userImage,
          garment_url: garmentUrl,
        });

        setProgress(20);
        const result = await pollStatus(response.job_id);
        return result;
      } catch (err: any) {
        const message = err.response?.data?.detail || err.message || "Error al generar";
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [pollStatus]
  );

  return { loading, error, resultImage, progress, generate, reset, setError };
}
