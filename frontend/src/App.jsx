import { Routes, Route } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import ProductDetail from "./pages/ProductDetail";
import VirtualTryOn from "./pages/VirtualTryOn";
import Profile from "./pages/Profile";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import NotFound from "./pages/NotFound";
import ChatFlotante from "./components/ChatFlotante";
import ModalVTON from "./components/ModalVTON";
import { closeVtonModal } from "./store/uiSlice";

function App() {
  const dispatch = useDispatch();
  const { vtonModal } = useSelector((state) => state.ui);

  return (
    <div className="min-h-screen bg-editorial-cream">
      <Navbar />
      <main className="pt-16">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/virtual-try-on" element={<VirtualTryOn />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <ChatFlotante />
      <ModalVTON
        product={vtonModal.product}
        isOpen={vtonModal.isOpen}
        onClose={() => dispatch(closeVtonModal)}
      />
    </div>
  );
}

export default App;
