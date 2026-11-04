import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import api from "@/lib/api";

interface Favorite {
  id: string;
  product_id: string;
  created_at: string;
  product?: {
    id: string;
    external_id: string;
    name: string;
    store: string;
    price: number;
    currency: string;
    image_url?: string;
    category: string;
    original_url: string;
  };
}

interface FavoritesState {
  items: Favorite[];
  total: number;
  page: number;
  limit: number;
  loading: boolean;
  error: string | null;
}

const initialState: FavoritesState = {
  items: [],
  total: 0,
  page: 1,
  limit: 20,
  loading: false,
  error: null,
};

export const fetchFavorites = createAsyncThunk(
  "favorites/fetchFavorites",
  async ({ page = 1, limit = 20 }: { page?: number; limit?: number }, { rejectWithValue }) => {
    try {
      const response = await api.get("/favorites", { params: { page, limit } });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || "Failed to fetch favorites");
    }
  }
);

export const addFavorite = createAsyncThunk(
  "favorites/addFavorite",
  async (productId: string, { rejectWithValue }) => {
    try {
      const response = await api.post(`/favorites/${productId}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || "Failed to add favorite");
    }
  }
);

export const removeFavorite = createAsyncThunk(
  "favorites/removeFavorite",
  async (productId: string, { rejectWithValue }) => {
    try {
      await api.delete(`/favorites/${productId}`);
      return productId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || "Failed to remove favorite");
    }
  }
);

export const checkFavorite = createAsyncThunk(
  "favorites/checkFavorite",
  async (productId: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/favorites/check/${productId}`);
      return { productId, isFavorite: response.data.is_favorite };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || "Failed to check favorite");
    }
  }
);

const favoritesSlice = createSlice({
  name: "favorites",
  initialState,
  reducers: {
    setPage: (state, action: PayloadAction<number>) => {
      state.page = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    optimisticAdd: (state, action: PayloadAction<Favorite>) => {
      state.items.unshift(action.payload);
      state.total += 1;
    },
    optimisticRemove: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((f) => f.product_id !== action.payload);
      state.total = Math.max(0, state.total - 1);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFavorites.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFavorites.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.favorites || [];
        state.total = action.payload.total || 0;
      })
      .addCase(fetchFavorites.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(addFavorite.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
        state.total += 1;
      })
      .addCase(addFavorite.rejected, (state, action) => {
        state.error = action.payload as string;
      })
      .addCase(removeFavorite.fulfilled, (state, action) => {
        state.items = state.items.filter((f) => f.product_id !== action.payload);
        state.total = Math.max(0, state.total - 1);
      })
      .addCase(removeFavorite.rejected, (state, action) => {
        state.error = action.payload as string;
      })
      .addCase(checkFavorite.fulfilled, (state, action) => {
        // Update local state if needed
      });
  },
});

export const { setPage, clearError, optimisticAdd, optimisticRemove } = favoritesSlice.actions;
export default favoritesSlice.reducer;