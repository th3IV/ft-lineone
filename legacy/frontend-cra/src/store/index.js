import { configureStore, createListenerMiddleware } from "@reduxjs/toolkit";
import userReducer from "./userSlice";
import productsReducer from "./productSlice";
import uiReducer from "./uiSlice";
import favoritesReducer from "./favoritesSlice";

const store = configureStore({
  reducer: {
    user: userReducer,
    products: productsReducer,
    ui: uiReducer,
    favorites: favoritesReducer,
  },
});

export default store;
