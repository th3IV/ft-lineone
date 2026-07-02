import { Link } from "react-router-dom";

function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-editorial-cream px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
        <p className="text-gray-500 text-lg mb-8">Página no encontrada</p>
        <Link
          to="/"
          className="bg-gradient-to-r from-fashion-pink to-fashion-purple text-white px-6 py-3 rounded-full font-semibold hover:opacity-90 transition-opacity"
        >
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}

export default NotFound;
