import { createSlice } from "@reduxjs/toolkit";

const loadFromStorage = () => {
  try {
    const saved = localStorage.getItem("outfitItems");
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
};

const outfitSlice = createSlice({
  name: "outfit",
  initialState: {
    items: loadFromStorage(),
  },
  reducers: {
    addItem: (state, action) => {
      state.items.push(action.payload);
      localStorage.setItem("outfitItems", JSON.stringify(state.items));
    },
    removeItem: (state, action) => {
      state.items = state.items.filter((item) => item.id !== action.payload);
      localStorage.setItem("outfitItems", JSON.stringify(state.items));
    },
    clearOutfit: (state) => {
      state.items = [];
      localStorage.removeItem("outfitItems");
    },
  },
});

export const { addItem, removeItem, clearOutfit } = outfitSlice.actions;
export default outfitSlice.reducer;
