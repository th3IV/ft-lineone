import api from "./api";

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const POLL_INTERVAL = 4000;
const POLL_TIMEOUT = 120000;

export const uploadImage = async (imageBase64) => {
  if (imageBase64 && imageBase64.length > MAX_IMAGE_BYTES * 1.37) {
    throw new Error(
      "La imagen es demasiado grande. Usa una imagen de menor resolución."
    );
  }
  const response = await api.post("/vton/upload", { image: imageBase64 });
  return response.data;
};

export const requestTryOn = async (product_id, user_image_url) => {
  const response = await api.post("/vton/try-on", {
    product_id,
    user_image_url,
  });
  return response.data;
};

export const getResult = async (vtonId) => {
  const response = await api.get(`/vton/result/${vtonId}`);
  return response.data;
};

export const pollResult = async (vtonId, onProgress) => {
  const startTime = Date.now();
  let attempt = 0;

  while (Date.now() - startTime < POLL_TIMEOUT) {
    attempt++;
    const elapsed = Math.round((Date.now() - startTime) / 1000);

    if (onProgress) {
      onProgress({ attempt, elapsed, status: "processing" });
    }

    try {
      const result = await getResult(vtonId);

      if (result.status === "completed" || result.output_image_url) {
        return result;
      }

      if (result.status === "failed") {
        throw new Error(
          result.error || "La generación del try-on falló. Intenta con otra foto."
        );
      }
    } catch (err) {
      if (err.response?.status === 404) {
        // Resultado aún no disponible, seguir esperando
      } else if (err.message?.includes("falló")) {
        throw err;
      }
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL));
  }

  throw new Error(
    "El proceso está tomando más tiempo del esperado. Intenta más tarde."
  );
};

export const getHistory = async () => {
  const response = await api.get("/vton/history");
  return response.data;
};
