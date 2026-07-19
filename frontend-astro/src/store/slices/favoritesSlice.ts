import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Product } from "../../lib/products";

interface FavoritesState {
  items: Product[];
  productIds: Set<string>;
  loading: boolean;
  error: string | null;
}

const initialState: FavoritesState = {
  items: [],
  productIds: new Set(),
  loading: false,
  error: null,
};

const favoritesSlice = createSlice({
  name: "favorites",
  initialState,
  reducers: {
    setFavorites: (state, action: PayloadAction<Product[]>) => {
      state.items = action.payload;
      state.productIds = new Set(action.payload.map((p) => p.id));
    },
    addFavorite: (state, action: PayloadAction<Product>) => {
      if (!state.productIds.has(action.payload.id)) {
        state.items.unshift(action.payload);
        state.productIds.add(action.payload.id);
      }
    },
    removeFavorite: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((p) => p.id !== action.payload);
      state.productIds.delete(action.payload);
    },
    toggleFavorite: (state, action: PayloadAction<Product>) => {
      if (state.productIds.has(action.payload.id)) {
        state.items = state.items.filter((p) => p.id !== action.payload.id);
        state.productIds.delete(action.payload.id);
      } else {
        state.items.unshift(action.payload);
        state.productIds.add(action.payload.id);
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  setFavorites,
  addFavorite,
  removeFavorite,
  toggleFavorite,
  setLoading,
  setError,
} = favoritesSlice.actions;
export default favoritesSlice.reducer;