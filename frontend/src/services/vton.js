import api from "./api";

export const requestTryOn = async (formData) => {
  const response = await api.post("/vton/try-on", formData);
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
