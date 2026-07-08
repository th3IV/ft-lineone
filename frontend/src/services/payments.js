import api from "./api";

export const createPayment = async () => {
  const response = await api.post("/payments/create", { plan_type: "premium" });
  return response.data;
};

export const getPaymentStatus = async () => {
  const response = await api.get("/payments/status");
  return response.data;
};
