import api from "./api";

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

export const login = async (email, password) => {
  const response = await api.post("/auth/login", { email, password });
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
  }
  if (response.data.refresh_token) {
    localStorage.setItem("refresh_token", response.data.refresh_token);
  }
  return response.data;
};

export const register = async (data) => {
  const response = await api.post("/auth/register", data);
  if (response.data.access_token) {
    localStorage.setItem("token", response.data.access_token);
  }
  if (response.data.refresh_token) {
    localStorage.setItem("refresh_token", response.data.refresh_token);
  }
  return response.data;
};

export const logout = async () => {
  const refresh_token = localStorage.getItem("refresh_token");
  try {
    await api.post("/auth/logout", { refresh_token });
  } catch {
    // Fail-open: limpiar tokens aunque el backend falle
  } finally {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
  }
};

export const getCurrentUser = async () => {
  const token = localStorage.getItem("token");
  if (!token) return null;

  try {
    const response = await api.get("/users/me");
    return response.data;
  } catch {
    // No fallback — let the 401 interceptor handle refresh/retry.
    // If /users/me fails, fetchProfile.rejected resets auth state.
    return null;
  }
};

export const refreshToken = async () => {
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    });
  }

  isRefreshing = true;

  const storedRefresh = localStorage.getItem("refresh_token");
  if (!storedRefresh) {
    isRefreshing = false;
    throw new Error("No refresh token available");
  }

  try {
    const response = await api.post("/auth/refresh", {
      refresh_token: storedRefresh,
    });
    if (response.data.access_token) {
      localStorage.setItem("token", response.data.access_token);
      if (response.data.refresh_token) {
        localStorage.setItem("refresh_token", response.data.refresh_token);
      }
    }
    processQueue(null, response.data.access_token);
    return response.data;
  } catch (error) {
    processQueue(error, null);
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    throw error;
  } finally {
    isRefreshing = false;
  }
};
