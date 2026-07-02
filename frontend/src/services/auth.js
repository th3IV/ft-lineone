import api from "./api";

export const login = async (email, password) => {
  const response = await api.post("/auth/login", { email, password });
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
  }
  return response.data;
};

export const register = async (data) => {
  const response = await api.post("/auth/register", data);
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
    const response = await api.get("/auth/me");
    return response.data;
  } catch {
    // Fallback: decode JWT payload locally (won't have name/measurements)
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload;
    } catch {
      localStorage.removeItem("token");
      return null;
    }
  }
};

export const refreshToken = async () => {
  const storedRefresh = localStorage.getItem("refresh_token");
  const response = await api.post("/auth/refresh", {
    refresh_token: storedRefresh,
  });
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
    localStorage.setItem("refresh_token", response.data.refresh_token);
  }
  return response.data;
};
