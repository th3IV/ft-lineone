import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import * as authService from "../services/auth";
import api from "../services/api";

export const loginUser = createAsyncThunk("user/login", async ({ email, password }, { rejectWithValue }) => {
  try {
    return await authService.login(email, password);
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Login failed");
  }
});

export const registerUser = createAsyncThunk("user/register", async (data, { rejectWithValue }) => {
  try {
    return await authService.register(data);
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Registration failed");
  }
});

export const fetchCurrentUser = createAsyncThunk("user/fetchCurrentUser", async (_, { rejectWithValue }) => {
  try {
    return await authService.getCurrentUser();
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to fetch user");
  }
});

export const updateMeasurements = createAsyncThunk("user/updateMeasurements", async (measurements, { rejectWithValue }) => {
  try {
    const response = await api.patch("/api/v1/auth/profile", { body_measurements: measurements });
    return response.data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to update measurements");
  }
});

export const updatePreferences = createAsyncThunk("user/updatePreferences", async (preferences, { rejectWithValue }) => {
  try {
    const response = await api.patch("/api/v1/auth/profile", { preferences });
    return response.data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to update preferences");
  }
});

const userSlice = createSlice({
  name: "user",
  initialState: {
    user: null,
    token: localStorage.getItem("token"),
    isAuthenticated: !!localStorage.getItem("token"),
    measurements: null,
    preferences: null,
    loading: false,
    error: null,
  },
  reducers: {
    logout(state) {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.measurements = null;
      state.preferences = null;
      authService.logout();
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        state.measurements = action.payload.measurements || null;
        state.preferences = action.payload.preferences || null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        if (action.payload.token) {
          state.user = action.payload.user;
          state.token = action.payload.token;
          state.isAuthenticated = true;
        }
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload.user || action.payload;
        state.measurements = action.payload.measurements || null;
        state.preferences = action.payload.preferences || null;
      })
      .addCase(updateMeasurements.fulfilled, (state, action) => {
        state.measurements = action.payload.measurements || action.payload;
      })
      .addCase(updatePreferences.fulfilled, (state, action) => {
        state.preferences = action.payload.preferences || action.payload;
      });
  },
});

export const { logout, clearError } = userSlice.actions;
export default userSlice.reducer;
