import { useState } from "react";
import { Link } from "react-router-dom";
import { useSelector } from "react-redux";

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated } = useSelector((state) => state.user);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center">
            <span className="text-xl font-bold text-gray-900">FT. THE LINE ONE</span>
          </Link>
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/catalog" className="text-gray-600 hover:text-gray-900 transition-colors">
              Catalog
            </Link>
             <Link to="/virtual-try-on" className="text-gray-600 hover:text-gray-900 transition-colors">
               Virtual Try-On
             </Link>
             {isAuthenticated ? (

              <Link to="/profile" className="text-gray-600 hover:text-gray-900 transition-colors">
                Profile
              </Link>
            ) : (
              <Link to="/login" className="text-gray-600 hover:text-gray-900 transition-colors">
                Sign In
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
            <Link to="/catalog" className="block px-3 py-2 text-gray-600 hover:text-gray-900" onClick={() => setIsOpen(false)}>
              Catalog
            </Link>
             <Link to="/virtual-try-on" className="block px-3 py-2 text-gray-600 hover:text-gray-900" onClick={() => setIsOpen(false)}>
               Virtual Try-On
             </Link>
             {isAuthenticated ? (

              <Link to="/profile" className="block px-3 py-2 text-gray-600 hover:text-gray-900" onClick={() => setIsOpen(false)}>
                Profile
              </Link>
            ) : (
              <Link to="/login" className="block px-3 py-2 text-gray-600 hover:text-gray-900" onClick={() => setIsOpen(false)}>
                Sign In
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
