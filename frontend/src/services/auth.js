import api from "./api";

export const login = async (email, password) => {
  const response = await api.post("/auth/login", { email, password });
  if (response.data.token) {
    localStorage.setItem("token", response.data.token);
  }
  return response.data;
};

export const register = async (data) => {
  const response = await api.post("/auth/register", data);
  return response.data;
};

export const logout = () => {
  localStorage.removeItem("token");
};

export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};

export const refreshToken = async () => {
  const response = await api.post("/auth/refresh");
  if (response.data.token) {
    localStorage.setItem("token", response.data.token);
  }
  return response.data;
};
