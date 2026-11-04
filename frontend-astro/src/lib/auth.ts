import api from "./api";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    name: string;
    is_premium: boolean;
    plan_type: string;
  };
}

interface RegisterData {
  email: string;
  name: string;
  password: string;
  age?: number;
}

export const login = async (email: string, password: string): Promise<LoginResponse> => {
  const response = await api.post("/auth/login", { email, password });
  return response.data;
};

export const register = async (data: RegisterData): Promise<LoginResponse> => {
  const response = await api.post("/auth/register", data);
  return response.data;
};

export const refreshToken = async (): Promise<{ access_token: string; refresh_token: string }> => {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) throw new Error("No refresh token");
  const response = await api.post("/auth/refresh", { refresh_token: refreshToken });
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get("/users/me");
  return response.data;
};

export const logout = async () => {
  const refreshToken = localStorage.getItem("refresh_token");
  if (refreshToken) {
    try {
      await api.post("/auth/logout", { refresh_token: refreshToken });
    } catch {
      // Ignore logout errors
    }
  }
  localStorage.removeItem("token");
  localStorage.removeItem("refresh_token");
};