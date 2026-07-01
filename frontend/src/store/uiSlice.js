import { createSlice } from "@reduxjs/toolkit";

const uiSlice = createSlice({
  name: "ui",
  initialState: {
    sidebarOpen: false,
    chatOpen: false,
    vtonModal: {
      isOpen: false,
      product: null,
    },
  },
  reducers: {
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen(state, action) {
      state.sidebarOpen = action.payload;
    },
    toggleChat(state) {
      state.chatOpen = !state.chatOpen;
    },
    openVtonModal(state, action) {
      state.vtonModal = { isOpen: true, product: action.payload };
      console.log("🛠️ Intentando abrir VTON. Producto recibido:", action.payload);

    },
    closeVtonModal(state) {
      state.vtonModal = { isOpen: false, product: null };
    },
  },
});

export const { toggleSidebar, setSidebarOpen, toggleChat, openVtonModal, closeVtonModal } =
  uiSlice.actions;
export default uiSlice.reducer;
