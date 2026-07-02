import api from "./api";

export const uploadImage = async (imageBase64) => {
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

export const getHistory = async () => {
  const response = await api.get("/vton/history");
  return response.data;
};
