import { createSlice } from "@reduxjs/toolkit";

const uiSlice = createSlice({
  name: "ui",
  initialState: {
    vtonModal: {
      isOpen: false,
      product: null,
    },
    upgradeModal: {
      isOpen: false,
    },
  },
  reducers: {
    openVtonModal(state, action) {
      state.vtonModal = { isOpen: true, product: action.payload };
    },
    closeVtonModal(state) {
      state.vtonModal = { isOpen: false, product: null };
    },
    openUpgradeModal(state) {
      state.upgradeModal = { isOpen: true };
    },
    closeUpgradeModal(state) {
      state.upgradeModal = { isOpen: false };
    },
  },
});

export const { openVtonModal, closeVtonModal, openUpgradeModal, closeUpgradeModal } = uiSlice.actions;
export default uiSlice.reducer;
