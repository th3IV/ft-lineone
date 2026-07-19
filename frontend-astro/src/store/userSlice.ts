import { configureStore, createSlice, PayloadAction } from "@reduxjs/toolkit";

interface UserState {
  user: {
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
  } | null;
  token: string | null;
  refresh_token: string | null;
  isAuthenticated: boolean;
  profileStatus: "idle" | "loading" | "succeeded" | "failed";
}

const initialState: UserState = {
  user: null,
  token: localStorage.getItem("token"),
  refresh_token: localStorage.getItem("refresh_token"),
  isAuthenticated: !!localStorage.getItem("token"),
  profileStatus: "idle",
};

const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<{ token: string; refresh_token: string; user: UserState["user"] }>) => {
      state.token = action.payload.token;
      state.refresh_token = action.payload.refresh_token;
      state.user = action.payload.user;
      state.isAuthenticated = true;
      localStorage.setItem("token", action.payload.token);
      localStorage.setItem("refresh_token", action.payload.refresh_token);
    },
    setUser: (state, action: PayloadAction<UserState["user"]>) => {
      state.user = action.payload;
    },
    setProfileStatus: (state, action: PayloadAction<UserState["profileStatus"]>) => {
      state.profileStatus = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refresh_token = null;
      state.isAuthenticated = false;
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
    },
    updateProfile: (state, action: PayloadAction<Partial<UserState["user"]>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    setPremium: (state, action: PayloadAction<boolean>) => {
      if (state.user) {
        state.user.is_premium = action.payload;
        state.user.plan_type = action.payload ? "premium" : "free";
      }
    },
  },
});

export const { setCredentials, setUser, setProfileStatus, logout, updateProfile, setPremium } = userSlice.actions;
export default userSlice.reducer;