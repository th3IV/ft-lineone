import axios from "axios";

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
    const config = error.config;

    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      if (onUnauthorized) {
        onUnauthorized();
      } else {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }

    if (
      !config.__isRetry &&
      (error.response?.status >= 500 ||
        error.code === "ECONNABORTED" ||
        error.code === "ERR_NETWORK")
    ) {
      config.__isRetry = true;
      const retryCount = config.__retryCount || 0;
      if (retryCount < 2) {
        config.__retryCount = retryCount + 1;
        const delay = Math.pow(2, retryCount) * 1000;
        await new Promise((resolve) => setTimeout(resolve, delay));
        return api(config);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
