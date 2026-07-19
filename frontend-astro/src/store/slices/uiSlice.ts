import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface UIState {
  isLoading: boolean;
  error: string | null;
  vtonModal: {
    isOpen: boolean;
    product: any | null;
  };
  upgradeModal: {
    isOpen: boolean;
    loading: boolean;
    error: string | null;
  };
  toast: {
    message: string;
    type: "success" | "error" | "info";
    visible: boolean;
  } | null;
}

const initialState: UIState = {
  isLoading: false,
  error: null,
  vtonModal: {
    isOpen: false,
    product: null,
  },
  upgradeModal: {
    isOpen: false,
    loading: false,
    error: null,
  },
  toast: null,
};

const uiSlice = createSlice({
  name: "ui",
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
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
    setUpgradeError: (state, action: PayloadAction<string | null>) => {
      state.upgradeModal.error = action.payload;
    },
    showToast: (state, action: PayloadAction<{ message: string; type: "success" | "error" | "info" }>) => {
      state.toast = {
        message: action.payload.message,
        type: action.payload.type,
        visible: true,
      };
    },
    hideToast: (state) => {
      state.toast = null;
    },
  },
});

export const {
  setLoading,
  setError,
  openVtonModal,
  closeVtonModal,
  openUpgradeModal,
  closeUpgradeModal,
  setUpgradeLoading,
  setUpgradeError,
  showToast,
  hideToast,
} = uiSlice.actions;
export default uiSlice.reducer;