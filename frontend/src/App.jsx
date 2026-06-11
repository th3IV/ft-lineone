import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Catalog from "./pages/Catalog";
import ProductDetail from "./pages/ProductDetail";
import VirtualTryOn from "./pages/VirtualTryOn";
import Profile from "./pages/Profile";

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="pt-16">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/virtual-try-on" element={<VirtualTryOn />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/login" element={<Home />} />
          <Route path="/register" element={<Home />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
