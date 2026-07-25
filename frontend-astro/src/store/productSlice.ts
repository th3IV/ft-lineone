import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import api from "@/lib/api";

interface Product {
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

interface ProductsState {
  items: Product[];
  total: number;
  page: number;
  limit: number;
  filters: {
    store?: string;
    category?: string;
    min_price?: number;
    max_price?: number;
    query?: string;
    gender?: string;
    clothing_type?: string;
    size?: string;
    color?: string;
    sort?: string;
  };
  loading: boolean;
  error: string | null;
}

const initialState: ProductsState = {
  items: [],
  total: 0,
  page: 1,
  limit: 20,
  filters: {},
  loading: false,
  error: null,
};

export const fetchProducts = createAsyncThunk(
  "products/fetchProducts",
  async ({ page = 1, limit = 20, filters = {} }: { page?: number; limit?: number; filters?: ProductsState["filters"] }, { rejectWithValue }) => {
    try {
      const params = new URLSearchParams();
      params.append("page", page.toString());
      params.append("limit", limit.toString());
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== "") params.append(key, value.toString());
      });
      const response = await api.get(`/products?${params.toString()}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || "Failed to fetch products");
    }
  }
);

export const searchProducts = createAsyncThunk(
  "products/searchProducts",
  async ({ query, limit = 20 }: { query: string; limit?: number }, { rejectWithValue }) => {
    try {
      const response = await api.get("/products/search", { params: { query, limit } });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || "Search failed");
    }
  }
);

export const getProduct = createAsyncThunk(
  "products/getProduct",
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/products/${id}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || "Product not found");
    }
  }
);

const productsSlice = createSlice({
  name: "products",
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<ProductsState["filters"]>) => {
      state.filters = action.payload;
      state.page = 1;
    },
    clearFilters: (state) => {
      state.filters = {};
      state.page = 1;
    },
    setPage: (state, action: PayloadAction<number>) => {
      state.page = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.products || [];
        state.total = action.payload.total || 0;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(searchProducts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchProducts.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.products || [];
        state.total = action.payload.total || 0;
      })
      .addCase(searchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(getProduct.pending, (state) => {
        state.loading = true;
      })
      .addCase(getProduct.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.items.findIndex((p) => p.id === action.payload.id);
        if (index >= 0) {
          state.items[index] = action.payload;
        } else {
          state.items.unshift(action.payload);
        }
      })
      .addCase(getProduct.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setFilters, clearFilters, setPage, clearError } = productsSlice.actions;
export default productsSlice.reducer;