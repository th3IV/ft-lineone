import { createSlice } from "@reduxjs/toolkit";

const uiSlice = createSlice({
  name: "ui",
  initialState: {
    vtonModal: {
      isOpen: false,
      product: null,
    },
  },
  reducers: {
    openVtonModal(state, action) {
      state.vtonModal = { isOpen: true, product: action.payload };
    },
    closeVtonModal(state) {
      state.vtonModal = { isOpen: false, product: null };
    },
  },
});

export const { openVtonModal, closeVtonModal } = uiSlice.actions;
export default uiSlice.reducer;
