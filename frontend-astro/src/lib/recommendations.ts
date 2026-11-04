import api from "./api";

export interface RecommendationRequest {
  query?: string;
}

export interface ChatRequest {
  question: string;
  product_id?: string;
  image?: string;
}

export interface Recommendation {
  product_id: string;
  reason: string;
}

export interface ChatResponse {
  advice: string;
  products: Array<{
    id: string;
    name: string;
    store: string;
    price: number;
    currency: string;
    category: string;
    image_url: string;
    image_urls: string[];
    sizes: string[];
    colors: string[];
    availability: boolean;
  }>;
  product_id?: string;
}

export const getRecommendations = async (query?: string): Promise<{
  user_id: string;
  recommendations: Array<{
    product_id: string;
    reason: string;
  }>;
  count: number;
}> => {
  const response = await api.get("/recommendations", { params: { query } });
  return response.data;
};

export const styleChat = async (data: ChatRequest): Promise<ChatResponse> => {
  const response = await api.post("/recommendations/chat", data);
  return response.data;
};