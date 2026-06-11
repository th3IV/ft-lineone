import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../services/api";

export const fetchRecommendations = createAsyncThunk(
  "recommendations/fetchRecommendations",
  async (productId, { rejectWithValue }) => {
    try {
      const params = productId ? { product_id: productId } : {};
      const response = await api.get("/recommendations", { params });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to fetch recommendations");
    }
  }
);

const recommendationSlice = createSlice({
  name: "recommendations",
  initialState: {
    recommendations: [],
    loading: false,
    error: null,
  },
  reducers: {
    clearRecommendations(state) {
      state.recommendations = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRecommendations.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRecommendations.fulfilled, (state, action) => {
        state.loading = false;
        state.recommendations = action.payload.recommendations || action.payload.products || action.payload;
      })
      .addCase(fetchRecommendations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearRecommendations } = recommendationSlice.actions;
export default recommendationSlice.reducer;
