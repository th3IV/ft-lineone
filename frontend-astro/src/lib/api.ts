import axios from "axios";

let onUnauthorized: (() => void) | null = null;

export const setUnauthorizedCallback = (cb: () => void) => {
  onUnauthorized = cb;
};

const api = axios.create({
  baseURL: import.meta.env.PUBLIC_API_URL || "https://api.thelineone.com/api/v1",
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
      if (originalRequest.url?.includes("/auth/refresh")) {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        if (onUnauthorized) onUnauthorized();
        else window.location.href = "/login";
        return Promise.reject(error);
      }

      originalRequest.__isRefreshRetry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const response = await axios.post(
          `${import.meta.env.PUBLIC_API_URL || "https://api.thelineone.com/api/v1"}/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token } = response.data;
        localStorage.setItem("token", access_token);
        localStorage.setItem("refresh_token", refresh_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        if (onUnauthorized) onUnauthorized();
        else window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    if (
      !originalRequest.__isRetry &&
      (error.code === "ECONNABORTED" || error.code === "ERR_NETWORK")
    ) {
      originalRequest.__isRetry = true;
      originalRequest.__retryCount = (originalRequest.__retryCount || 0) + 1;
      if (originalRequest.__retryCount <= 2) {
        const delay = Math.pow(2, originalRequest.__retryCount - 1) * 1000;
        await new Promise((resolve) => setTimeout(resolve, delay));
        return api(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export default api;