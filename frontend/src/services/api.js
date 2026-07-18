import axios from "axios";
import { refreshToken } from "./auth";

let onUnauthorized = null;

export const setUnauthorizedCallback = (cb) => {
  onUnauthorized = cb;
};

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "https://api.thelineone.com/api/v1",
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest.__isRefreshRetry) {
      // Skip refresh for the refresh endpoint itself (avoid re-entrant deadlock)
      if (originalRequest.url?.includes("/auth/refresh")) {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        if (onUnauthorized) {
          onUnauthorized();
        } else {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
      originalRequest.__isRefreshRetry = true;
      try {
        await refreshToken();
        return api(originalRequest);
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        if (onUnauthorized) {
          onUnauthorized();
        } else {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    }

    if (
      !originalRequest.__isRetry &&
      (error.code === "ECONNABORTED" || error.code === "ERR_NETWORK")
    ) {
      const newConfig = { ...originalRequest };
      newConfig.__isRetry = true;
      newConfig.__retryCount = (originalRequest.__retryCount || 0) + 1;
      if (newConfig.__retryCount <= 2) {
        const delay = Math.pow(2, newConfig.__retryCount - 1) * 1000;
        await new Promise((resolve) => setTimeout(resolve, delay));
        return api(newConfig);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
