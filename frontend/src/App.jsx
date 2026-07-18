import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { useEffect, lazy, Suspense } from "react";
import React from "react";
import Navbar from "./components/Navbar";
import PageTransition from "./components/PageTransition";
import ErrorBoundary from "./components/ErrorBoundary";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import ProductDetail from "./pages/ProductDetail";
import ChatFlotante from "./components/ChatFlotante";
import ModalVTON from "./components/ModalVTON";
import { closeVtonModal } from "./store/uiSlice";
import { setUnauthorizedCallback } from "./services/api";
import api from "./services/api";
import { logoutUser, fetchProfile } from "./store/userSlice";
import { fetchFavorites } from "./store/favoritesSlice";

const VirtualTryOn = lazy(() => import("./pages/VirtualTryOn"));
const Profile = lazy(() => import("./pages/Profile"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const OnboardingQuiz = lazy(() => import("./pages/OnboardingQuiz"));
const NotFound = lazy(() => import("./pages/NotFound"));
const SuccessPage = lazy(() => import("./pages/SuccessPage"));

function PageLoader() {
  return (
    <div className="min-h-screen bg-editorial-cream flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-editorial-black" />
    </div>
  );
}

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
  const { isAuthenticated, user, profileStatus } = useSelector((state) => state.user);
  const isPremium = user?.is_premium || user?.plan_type === "premium";

  useEffect(() => {
    setUnauthorizedCallback(() => {
      dispatch(logoutUser());
      navigate("/login");
    });
  }, [dispatch, navigate]);

  useEffect(() => {
    if (isAuthenticated && profileStatus === "idle") {
      dispatch(fetchProfile());
    }
  }, [dispatch, isAuthenticated, profileStatus]);

  useEffect(() => {
    if (isAuthenticated && profileStatus === "succeeded") {
      dispatch(fetchFavorites());
    }
  }, [dispatch, isAuthenticated, profileStatus]);

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
          <ErrorBoundary>
            <Suspense fallback={<PageLoader />}>
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
            </Suspense>
          </ErrorBoundary>
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
