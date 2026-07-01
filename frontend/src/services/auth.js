import api from "./api";

export const login = async (email, password) => {
  // --- CÓDIGO TEMPORAL PARA SALTAR EL LOGIN REAL ---
  console.log("Simulando inicio de sesión...");
  
  // Guardamos un token falso para engañar a las rutas protegidas
  const fakeToken = "token-falso-de-prueba-123";
  localStorage.setItem("token", fakeToken);
  
  // Devolvemos un objeto simulando la respuesta de tu backend
  return {
    message: "Login exitoso",
    token: fakeToken,
    user: { id: 1, email: email, name: "Usuario de Prueba" }
  };
};
/*export const login = async (email, password) => {
  const response = await api.post("/auth/login", { email, password });
  if (response.data.token) {
    localStorage.setItem("token", response.data.token);
  }
  return response.data;
};*/

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
