import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Product } from "../../lib/products";

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
    sort?: "price_asc" | "price_desc" | "newest";
  };
  loading: boolean;
  error: string | null;
  selectedProduct: Product | null;
  stores: string[];
  categories: string[];
}

const initialState: ProductsState = {
  items: [],
  total: 0,
  page: 1,
  limit: 20,
  filters: {},
  loading: false,
  error: null,
  selectedProduct: null,
  stores: [],
  categories: [],
};

const productsSlice = createSlice({
  name: "products",
  initialState,
  reducers: {
    setProducts: (state, action: PayloadAction<{ items: Product[]; total: number; page: number; limit: number }>) => {
      state.items = action.payload.items;
      state.total = action.payload.total;
      state.page = action.payload.page;
      state.limit = action.payload.limit;
    },
    setFilters: (state, action: PayloadAction<Partial<typeof initialState.filters>>) => {
      state.filters = { ...state.filters, ...action.payload };
      state.page = 1;
    },
    clearFilters: (state) => {
      state.filters = {};
      state.page = 1;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setSelectedProduct: (state, action: PayloadAction<Product | null>) => {
      state.selectedProduct = action.payload;
    },
    setStores: (state, action: PayloadAction<string[]>) => {
      state.stores = action.payload;
    },
    setCategories: (state, action: PayloadAction<string[]>) => {
      state.categories = action.payload;
    },
  },
});

export const {
  setProducts,
  setFilters,
  clearFilters,
  setLoading,
  setError,
  setSelectedProduct,
  setStores,
  setCategories,
} = productsSlice.actions;
export default productsSlice.reducer;