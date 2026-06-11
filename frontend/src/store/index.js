import { configureStore } from "@reduxjs/toolkit";
import userReducer from "./userSlice";
import productsReducer from "./productSlice";
import recommendationsReducer from "./recommendationSlice";

const store = configureStore({
  reducer: {
    user: userReducer,
    products: productsReducer,
    recommendations: recommendationsReducer,
  },
});

export default store;
