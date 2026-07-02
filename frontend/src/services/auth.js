import api from "./api";

export const login = async (email, password) => {
  const response = await api.post("/api/v1/auth/login", { email, password });
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
  }
  return response.data;
};

export const register = async (data) => {
  const response = await api.post("/api/v1/auth/register", data);
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
  }
  return response.data;
};

export const logout = () => {
  localStorage.removeItem("token");
};

export const getCurrentUser = async () => {
  const token = localStorage.getItem("token");
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload;
  } catch {
    localStorage.removeItem("token");
    return null;
  }
};

export const refreshToken = async () => {
  const response = await api.post("/api/v1/auth/refresh");
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
  }
  return response.data;
};
