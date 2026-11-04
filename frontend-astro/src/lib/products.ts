import api from "./api";

export interface Product {
  id: string;
  external_id: string;
  name: string;
  store: string;
  price: number;
  currency: string;
  category: string;
  description: string;
  original_url: string;
  image_url: string;
  image_urls: string[];
  sizes: string[];
  colors: string[];
  availability: boolean;
  created_at: string;
}

export interface ProductFilters {
  store?: string;
  category?: string;
  min_price?: number;
  max_price?: number;
  query?: string;
  gender?: string;
  clothing_type?: string;
  size?: string;
  color?: string;
  sort?: "price_asc" | "price_desc" | "newest";
}

export interface PaginatedResponse<T> {
  results: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export const getProducts = async (filters: ProductFilters = {}, page = 1, limit = 20): Promise<PaginatedResponse<Product>> => {
  const response = await api.get("/products", { params: { ...filters, page, limit } });
  return response.data;
};

export const getProduct = async (id: string): Promise<Product> => {
  const response = await api.get(`/products/${id}`);
  return response.data;
};

export const searchProducts = async (query: string, limit = 20): Promise<Product[]> => {
  const response = await api.get("/products/search", { params: { q: query, limit } });
  return response.data;
};

export const getStores = async (): Promise<string[]> => {
  const response = await api.get("/products/stores");
  return response.data;
};

export const getCategories = async (): Promise<string[]> => {
  const response = await api.get("/products/categories");
  return response.data;
};