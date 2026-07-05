import { configureStore } from "@reduxjs/toolkit";
import userReducer from "./userSlice";
import productsReducer from "./productSlice";
import recommendationsReducer from "./recommendationSlice";
import uiReducer from "./uiSlice";
import favoritesReducer from "./favoritesSlice";

const store = configureStore({
  reducer: {
    user: userReducer,
    products: productsReducer,
    recommendations: recommendationsReducer,
    ui: uiReducer,
    favorites: favoritesReducer,
  },
});

export default store;
