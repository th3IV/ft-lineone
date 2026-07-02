import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../services/api";

export const fetchProducts = createAsyncThunk("products/fetchProducts", async (params, { rejectWithValue }) => {
  try {
    const response = await api.get("/products", { params });
    return response.data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to fetch products");
  }
});

export const fetchProductById = createAsyncThunk("products/fetchProductById", async (id, { rejectWithValue }) => {
  try {
    const response = await api.get(`/products/${id}`);
    return response.data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to fetch product");
  }
});

export const searchProducts = createAsyncThunk("products/searchProducts", async (query, { rejectWithValue }) => {
  try {
    const response = await api.get("/products/search", { params: { q: query } });
    return response.data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Search failed");
  }
});

const productSlice = createSlice({
  name: "products",
  initialState: {
    products: [],
    selectedProduct: null,
    filters: {
      gender: null,
      clothingType: [],
      size: null,
      color: null,
      store: null,
      minPrice: null,
      maxPrice: null,
      query: null,
    },
    pagination: { page: 1, limit: 20, total: 0 },
    loading: false,
    error: null,
  },
  reducers: {
    setFilters(state, action) {
      const { page, ...filters } = action.payload;
      state.filters = { ...state.filters, ...filters };
      if (page !== undefined) {
        state.pagination.page = page;
      }
    },
    setPage(state, action) {
      state.pagination.page = action.payload;
    },
    clearFilters(state) {
      state.filters = {
        gender: null,
        clothingType: [],
        size: null,
        color: null,
        store: null,
        minPrice: null,
        maxPrice: null,
        query: null,
      };
      state.pagination.page = 1;
      state.pagination.total = 0;
    },
    clearSelectedProduct(state) {
      state.selectedProduct = null;
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
        state.products = action.payload.products || action.payload.items || action.payload;
        state.pagination.total = action.payload.total || action.payload.count || state.products.length;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchProductById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProductById.fulfilled, (state, action) => {
        state.loading = false;
        state.selectedProduct = action.payload.product || action.payload;
      })
      .addCase(fetchProductById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(searchProducts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchProducts.fulfilled, (state, action) => {
        state.loading = false;
        state.products = action.payload.products || action.payload.items || action.payload;
      })
      .addCase(searchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setFilters, setPage, clearFilters, clearSelectedProduct } = productSlice.actions;
export default productSlice.reducer;
