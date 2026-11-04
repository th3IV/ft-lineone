import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../services/api";

export const fetchFavorites = createAsyncThunk(
  "favorites/fetch",
  async (_, { rejectWithValue }) => {
    try {
      const res = await api.get("/favorites");
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to fetch favorites");
    }
  }
);

export const toggleFavorite = createAsyncThunk(
  "favorites/toggle",
  async (productId, { getState, rejectWithValue }) => {
    try {
      const { favorites } = getState().favorites;
      const isFav = favorites.includes(productId);
      if (isFav) {
        await api.delete(`/favorites/${productId}`);
        return { productId, is_favorite: false };
      } else {
        await api.post(`/favorites/${productId}`);
        return { productId, is_favorite: true };
      }
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to update favorite");
    }
  }
);

const favoritesSlice = createSlice({
  name: "favorites",
  initialState: {
    favorites: [],
    products: [],
    total: 0,
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchFavorites.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchFavorites.fulfilled, (state, action) => {
        state.loading = false;
        state.products = action.payload.products;
        state.favorites = action.payload.products.map((p) => p.id);
        state.total = action.payload.total;
      })
      .addCase(fetchFavorites.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(toggleFavorite.fulfilled, (state, action) => {
        const { productId, is_favorite } = action.payload;
        if (is_favorite) {
          if (!state.favorites.includes(productId)) {
            state.favorites.push(productId);
          }
        } else {
          state.favorites = state.favorites.filter((id) => id !== productId);
          state.products = state.products.filter((p) => p.id !== productId);
          state.total = state.products.length;
        }
      });
  },
});

export default favoritesSlice.reducer;
