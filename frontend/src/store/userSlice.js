import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import * as authService from "../services/auth";
import api from "../services/api";

export const logoutUser = createAsyncThunk("user/logout", async () => {
  await authService.logout();
});

export const loginUser = createAsyncThunk("user/login", async ({ email, password }, { rejectWithValue }) => {
  try {
    const data = await authService.login(email, password);
    if (data.refresh_token) {
      localStorage.setItem("refresh_token", data.refresh_token);
    }
    return data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Login failed");
  }
});

export const registerUser = createAsyncThunk("user/register", async (data, { rejectWithValue }) => {
  try {
    const result = await authService.register(data);
    if (result.refresh_token) {
      localStorage.setItem("refresh_token", result.refresh_token);
    }
    return result;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Registration failed");
  }
});

export const fetchProfile = createAsyncThunk("user/fetchProfile", async (_, { rejectWithValue }) => {
  try {
    return await authService.getCurrentUser();
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to fetch profile");
  }
});

export const updateProfile = createAsyncThunk("user/updateProfile", async (data, { rejectWithValue }) => {
  try {
    const response = await api.put("/users/profile", {
      name: data.name,
      gender: data.gender,
    });
    return { ...response.data, name: data.name, gender: data.gender };
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to update profile");
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
    const response = await api.put("/users/measurements", measurements);
    return response.data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || "Failed to update measurements");
  }
});

export const updatePreferences = createAsyncThunk("user/updatePreferences", async (preferences, { rejectWithValue }) => {
  try {
    const response = await api.put("/users/preferences", preferences);
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
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.measurements = null;
        state.preferences = null;
      })
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        state.measurements = action.payload.user?.body_measurements || null;
        state.preferences = action.payload.user?.preferences || null;
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
        if (action.payload.access_token) {
          state.user = action.payload.user;
          state.token = action.payload.access_token;
          state.isAuthenticated = true;
        }
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload.user || action.payload;
        state.measurements = action.payload.measurements || action.payload.user?.body_measurements || null;
        state.preferences = action.payload.preferences || action.payload.user?.preferences || null;
      })
      .addCase(updateMeasurements.fulfilled, (state, action) => {
        state.measurements = action.payload.measurements || {};
      })
      .addCase(updatePreferences.fulfilled, (state, action) => {
        state.preferences = action.payload.preferences || {};
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        const data = action.payload;
        state.user = {
          id: data.id,
          email: data.email,
          name: data.name,
          gender: data.gender || "",
          created_at: data.created_at,
        };
        state.measurements = data.body_measurements || {};
        state.preferences = data.preferences || {};
      })
      .addCase(updateProfile.fulfilled, (state, action) => {
        if (state.user) {
          if (action.payload.name) state.user.name = action.payload.name;
          if (action.payload.gender !== undefined) state.user.gender = action.payload.gender;
        }
      });
  },
});

export const { clearError } = userSlice.actions;
export default userSlice.reducer;
