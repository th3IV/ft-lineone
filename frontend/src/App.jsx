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
import OnboardingQuiz from "./pages/OnboardingQuiz";
import NotFound from "./pages/NotFound";
import SuccessPage from "./pages/SuccessPage";
import ChatFlotante from "./components/ChatFlotante";
import ModalVTON from "./components/ModalVTON";
import { closeVtonModal } from "./store/uiSlice";
import { setUnauthorizedCallback } from "./services/api";
import api from "./services/api";
import { logoutUser } from "./store/userSlice";
import { fetchFavorites } from "./store/favoritesSlice";

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
  const { isAuthenticated, user } = useSelector((state) => state.user);
  const isPremium = user?.is_premium || user?.plan_type === "premium";

  useEffect(() => {
    setUnauthorizedCallback(() => {
      dispatch(logoutUser());
      navigate("/login");
    });
  }, [dispatch, navigate]);

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchFavorites());
    }
  }, [dispatch, isAuthenticated]);

  // Trigger scrapers on first visit (once per session)
  useEffect(() => {
    const scrapersTriggered = sessionStorage.getItem("scrapers_triggered");
    if (!scrapersTriggered) {
      sessionStorage.setItem("scrapers_triggered", "true");
      api.post("/scrapers/trigger").catch(() => {});
    }
  }, []);

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
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <OnboardingQuiz />
                </ProtectedRoute>
              }
            />
            <Route
              path="/payment/success"
              element={
                <ProtectedRoute>
                  <SuccessPage />
                </ProtectedRoute>
              }
            />
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
