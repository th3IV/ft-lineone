import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { useEffect } from "react";
import Navbar from "./components/Navbar";
import PageTransition from "./components/PageTransition";
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
import { setUnauthorizedCallback } from "./services/api";
import { logoutUser } from "./store/userSlice";

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useSelector((state) => state.user);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { vtonModal } = useSelector((state) => state.ui);

  useEffect(() => {
    setUnauthorizedCallback(() => {
      dispatch(logoutUser());
      navigate("/login");
    });
  }, [dispatch, navigate]);

  return (
    <div className="min-h-screen bg-editorial-cream">
      <Navbar />
      <main className="pt-14">
        <PageTransition>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/catalog" element={<Catalog />} />
            <Route path="/product/:id" element={<ProductDetail />} />
            <Route
              path="/virtual-try-on"
              element={
                <ProtectedRoute>
                  <VirtualTryOn />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </PageTransition>
      </main>
      <ChatFlotante />
      <ModalVTON
        product={vtonModal.product}
        isOpen={vtonModal.isOpen}
        onClose={() => dispatch(closeVtonModal())}
      />
    </div>
  );
}

export default App;
