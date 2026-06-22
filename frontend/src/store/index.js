import { configureStore } from "@reduxjs/toolkit";
import userReducer from "./userSlice";
import productsReducer from "./productSlice";
import recommendationsReducer from "./recommendationSlice";
import outfitReducer from "./outfitSlice";

const store = configureStore({
  reducer: {
    user: userReducer,
    products: productsReducer,
    recommendations: recommendationsReducer,
    outfit: outfitReducer,
  },
});

export default store;
