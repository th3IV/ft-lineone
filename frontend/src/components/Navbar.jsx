import { useState } from "react";
import { Link } from "react-router-dom";
import { useSelector } from "react-redux";

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated } = useSelector((state) => state.user);
  const outfitCount = useSelector((state) => state.outfit?.items?.length || 0);

  const navLinks = [
    { to: "/", label: "Inicio" },
    { to: "/catalog", label: "Catálogo" },
    { to: "/outfit-builder", label: "Armar Outfit", badge: outfitCount > 0 ? outfitCount : null },
    { to: "/virtual-try-on", label: "Probador Virtual" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xs">FT</span>
            </div>
            <span className="text-lg font-bold text-gray-900 hidden sm:block">FT. THE LINE ONE</span>
          </Link>

          <div className="hidden md:flex items-center space-x-6">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="relative text-sm text-gray-600 hover:text-indigo-600 transition-colors font-medium"
              >
                {link.label}
                {link.badge && (
                  <span className="absolute -top-2 -right-3 bg-indigo-600 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                    {link.badge}
                  </span>
                )}
              </Link>
            ))}
            {isAuthenticated ? (
              <Link
                to="/profile"
                className="text-sm text-gray-600 hover:text-indigo-600 transition-colors font-medium"
              >
                Perfil
              </Link>
            ) : (
              <Link
                to="/login"
                className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                Ingresar
              </Link>
            )}
          </div>

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="md:hidden bg-white border-t">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-indigo-600"
                onClick={() => setIsOpen(false)}
              >
                {link.label}
                {link.badge && (
                  <span className="bg-indigo-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {link.badge}
                  </span>
                )}
              </Link>
            ))}
            {isAuthenticated ? (
              <Link
                to="/profile"
                className="block px-3 py-2 text-gray-600 hover:text-indigo-600"
                onClick={() => setIsOpen(false)}
              >
                Perfil
              </Link>
            ) : (
              <Link
                to="/login"
                className="block px-3 py-2 text-indigo-600 font-medium"
                onClick={() => setIsOpen(false)}
              >
                Ingresar
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
