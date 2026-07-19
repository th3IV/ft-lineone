export interface Product {
  id: string;
  external_id: string;
  store: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  original_url: string;
  image_url?: string;
  image_urls: string[];
  category: string;
  sizes: string[];
  colors: string[];
  availability: boolean;
  created_at: string;
}

export interface ProductsResponse {
  products: Product[];
  total: number;
  page: number;
  limit: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  is_premium: boolean;
  plan_type: "free" | "premium";
  body_measurements?: Record<string, any>;
  preferences?: Record<string, any>;
  profile_image?: string;
  age?: number;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  refresh_token: string;
  user: User;
}

export interface VtonJob {
  id: string;
  status: "pending" | "processing" | "completed" | "failed";
  input_image_url: string;
  output_image_url?: string;
  garment_image_url?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface VtonStartResponse {
  job_id: string;
  status: "pending";
  daily_usage: {
    vton: number;
    llm: number;
    limit: number;
    plan_type: "free" | "premium";
  };
}

export interface Favorite {
  id: string;
  product_id: string;
  created_at: string;
  product?: Product;
}

export interface FavoritesResponse {
  favorites: Favorite[];
  total: number;
  page: number;
  limit: number;
}

export interface PaymentResponse {
  token: string;
  url: string;
  buy_order: string;
}

export interface PaymentStatus {
  is_premium: boolean;
  plan_type: "free" | "premium";
  last_payment?: {
    status: string;
    period_end: string;
    amount: number;
  };
}