import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface UIState {
  vtonModal: {
    isOpen: boolean;
    product: any | null;
  };
  upgradeModal: {
    isOpen: boolean;
    loading: boolean;
    error: string | null;
  };
  toasts: Array<{
    id: string;
    message: string;
    type: "success" | "error" | "info";
  }>;
  mobileMenuOpen: boolean;
  profileDrawerOpen: boolean;
  chatOpen: boolean;
  sidebarOpen: boolean;
}

const initialState: UIState = {
  vtonModal: {
    isOpen: false,
    product: null,
  },
  upgradeModal: {
    isOpen: false,
    loading: false,
    error: null,
  },
  toasts: [],
  mobileMenuOpen: false,
  profileDrawerOpen: false,
  chatOpen: false,
  sidebarOpen: true,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    openVtonModal: (state, action: PayloadAction<any>) => {
      state.vtonModal.isOpen = true;
      state.vtonModal.product = action.payload;
    },
    closeVtonModal: (state) => {
      state.vtonModal.isOpen = false;
      state.vtonModal.product = null;
    },
    openUpgradeModal: (state) => {
      state.upgradeModal.isOpen = true;
      state.upgradeModal.error = null;
    },
    closeUpgradeModal: (state) => {
      state.upgradeModal.isOpen = false;
      state.upgradeModal.error = null;
    },
    setUpgradeLoading: (state, action: PayloadAction<boolean>) => {
      state.upgradeModal.loading = action.payload;
    },
    setUpgradeError: (state, action: PayloadAction<string>) => {
      state.upgradeModal.error = action.payload;
    },
    addToast: (state, action: PayloadAction<{ message: string; type: "success" | "error" | "info" }>) => {
      const id = Math.random().toString(36).substring(7);
      state.toasts.push({ id, ...action.payload });
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
    clearToasts: (state) => {
      state.toasts = [];
    },
    toggleMobileMenu: (state) => {
      state.mobileMenuOpen = !state.mobileMenuOpen;
    },
    setMobileMenuOpen: (state, action: PayloadAction<boolean>) => {
      state.mobileMenuOpen = action.payload;
    },
    toggleProfileDrawer: (state) => {
      state.profileDrawerOpen = !state.profileDrawerOpen;
    },
    setProfileDrawerOpen: (state, action: PayloadAction<boolean>) => {
      state.profileDrawerOpen = action.payload;
    },
    toggleChat: (state) => {
      state.chatOpen = !state.chatOpen;
    },
    setChatOpen: (state, action: PayloadAction<boolean>) => {
      state.chatOpen = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
  },
});

export const {
  openVtonModal,
  closeVtonModal,
  openUpgradeModal,
  closeUpgradeModal,
  setUpgradeLoading,
  setUpgradeError,
  addToast,
  removeToast,
  clearToasts,
  toggleMobileMenu,
  setMobileMenuOpen,
  toggleProfileDrawer,
  setProfileDrawerOpen,
  toggleChat,
  setChatOpen,
  toggleSidebar,
  setSidebarOpen,
} = uiSlice.actions;

export default uiSlice.reducer;