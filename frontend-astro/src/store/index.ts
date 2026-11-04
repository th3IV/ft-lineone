import { configureStore } from "@reduxjs/toolkit";
import userReducer from "./userSlice";
import uiReducer from "./uiSlice";
import productsReducer from "./productSlice";
import favoritesReducer from "./favoritesSlice";

export const store = configureStore({
  reducer: {
    user: userReducer,
    ui: uiReducer,
    products: productsReducer,
    favorites: favoritesReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;