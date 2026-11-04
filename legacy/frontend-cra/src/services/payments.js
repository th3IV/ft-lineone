import api from "./api";

export const createPayment = async () => {
  const response = await api.post("/payments/create", { plan_type: "premium" });
  return response.data;
};

export const confirmPayment = async (token) => {
  const response = await api.post("/payments/confirm", { token });
  return response.data;
};

export const getPaymentStatus = async () => {
  const response = await api.get("/payments/status");
  return response.data;
};

export function redirectToWebpay(url, token) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = url;

  const input = document.createElement("input");
  input.type = "hidden";
  input.name = "token_ws";
  input.value = token;
  form.appendChild(input);

  document.body.appendChild(form);
  form.submit();
}
