import { Provider } from "react-redux";
import { store } from "@/store";
import { VirtualTryOn } from "./VirtualTryOn";

interface VirtualTryOnAppProps {
  productId?: string;
  initialProduct?: any;
}

/** Wraps the island with the Redux store — hooks crash without a Provider. */
export const VirtualTryOnApp = (props: VirtualTryOnAppProps) => (
  <Provider store={store}>
    <VirtualTryOn {...props} />
  </Provider>
);

export default VirtualTryOnApp;
