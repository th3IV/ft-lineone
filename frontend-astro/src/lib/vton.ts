import api from "./api";

export interface VtonStartRequest {
  product_id: string;
  image: string;
  garment_url?: string;
}

export interface VtonStartResponse {
  job_id: string;
  status: string;
  daily_usage: {
    vton: number;
    llm: number;
    limit: number;
    plan_type: string;
  };
}

export interface VtonStatusResponse {
  status: "pending" | "processing" | "completed" | "failed";
  output_image_url?: string;
  error?: string;
}

export interface VtonHistoryEntry {
  id: string;
  status: string;
  product_id: string;
  input_image_url: string;
  output_image_url?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  product?: {
    id: string;
    name: string;
    image: string;
    store: string;
    price: number;
    original_url: string;
  };
}

export const startVton = async (data: VtonStartRequest): Promise<VtonStartResponse> => {
  const response = await api.post("/vton/start", data);
  return response.data;
};

export const getVtonStatus = async (jobId: string): Promise<VtonStatusResponse> => {
  const response = await api.get(`/vton/status/${jobId}`);
  return response.data;
};

export const getVtonHistory = async (limit = 20, page = 1): Promise<{ results: VtonHistoryEntry[]; total: number }> => {
  const response = await api.get("/vton/history", { params: { limit, page } });
  return response.data;
};

export const uploadPresignedUrl = async (contentType = "image/jpeg", folder = "vton"): Promise<{
  upload_url: string;
  get_url: string;
  key: string;
  expires_in: number;
}> => {
  const response = await api.post("/vton/upload-url", { content_type: contentType, folder });
  return response.data;
};