import { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { loginUser, logout } from "../store/userSlice";

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const menuRef = useRef(null);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, isAuthenticated, loading, error } = useSelector((state) => state.user);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogin = (e) => {
    e.preventDefault();
    dispatch(loginUser({ email, password })).then((res) => {
      if (res.meta.requestStatus === "fulfilled") {
        setEmail("");
        setPassword("");
        setUserMenuOpen(false);
      }
    });
  };

  const handleLogout = () => {
    dispatch(logout());
    setUserMenuOpen(false);
    navigate("/");
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 group">
            <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-fashion-pink to-fashion-purple flex items-center justify-center text-white text-xs font-bold">
              FT
            </span>
            <span className="text-lg font-serif font-bold bg-gradient-to-r from-fashion-pink to-fashion-purple bg-clip-text text-transparent">
              THE LINE ONE
            </span>
          </Link>
          <div className="hidden md:flex items-center space-x-1">
            {[
              { to: "/catalog", label: "Catálogo" },
            ].map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-fashion-pink rounded-xl hover:bg-fashion-pink-light transition-all duration-200"
              >
                {label}
              </Link>
            ))}

            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="ml-2 w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-200 border-2 border-transparent hover:border-fashion-pink"
              >
                {isAuthenticated && user?.name ? (
                  <span className="w-full h-full rounded-full bg-gradient-to-br from-fashion-pink to-fashion-purple text-white flex items-center justify-center text-xs">
                    {user.name.charAt(0).toUpperCase()}
                  </span>
                ) : (
                  <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                )}
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-72 bg-white/95 backdrop-blur-lg rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-fade-in">
                  {isAuthenticated ? (
                    <div className="p-5">
                      <div className="flex items-center gap-3 mb-4 pb-4 border-b border-gray-100">
                        <span className="w-10 h-10 rounded-full bg-gradient-to-br from-fashion-pink to-fashion-purple text-white flex items-center justify-center text-sm font-bold">
                          {user?.name?.charAt(0).toUpperCase() || "U"}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-900 truncate">{user?.name || "Usuario"}</p>
                          <p className="text-xs text-gray-500 truncate">{user?.email || ""}</p>
                        </div>
                      </div>
                      <Link
                        to="/profile"
                        onClick={() => setUserMenuOpen(false)}
                        className="block w-full text-center px-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-fashion-pink to-fashion-purple rounded-xl hover:opacity-90 transition-all mb-2"
                      >
                        Mi Perfil
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="block w-full text-center px-4 py-2.5 text-sm font-medium text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all"
                      >
                        Cerrar sesión
                      </button>
                    </div>
                  ) : (
                    <form onSubmit={handleLogin} className="p-5 space-y-4">
                      <div className="text-center">
                        <h3 className="text-lg font-serif font-semibold text-gray-900">Iniciar Sesión</h3>
                        <p className="text-xs text-gray-500 mt-1">Ingresa tus credenciales</p>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Usuario / Email</label>
                        <input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="tu@email.com"
                          required
                          className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm bg-white focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Contraseña</label>
                        <input
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="••••••••"
                          required
                          className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm bg-white focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all"
                        />
                      </div>
                      {error && (
                        <p className="text-xs text-red-500 text-center">{error}</p>
                      )}
                      <button
                        type="submit"
                        disabled={loading}
                        className="w-full px-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-fashion-pink to-fashion-purple rounded-xl hover:opacity-90 transition-all disabled:opacity-60 flex items-center justify-center gap-2"
                      >
                        {loading ? (
                          <>
                            <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                            Ingresando...
                          </>
                        ) : (
                          "Ingresar"
                        )}
                      </button>
                      <p className="text-xs text-center text-gray-500">
                        ¿No tienes cuenta?{" "}
                        <Link to="/register" className="text-fashion-pink font-medium hover:underline" onClick={() => setUserMenuOpen(false)}>
                          Regístrate
                        </Link>
                      </p>
                    </form>
                  )}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-xl text-gray-600 hover:text-fashion-pink hover:bg-fashion-pink-light transition-all"
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
        <div className="md:hidden bg-white/95 backdrop-blur-lg border-t border-gray-100">
          <div className="px-4 pt-2 pb-4 space-y-1">
            {[
              { to: "/catalog", label: "Catálogo" },
              { to: isAuthenticated ? "/profile" : "/login", label: isAuthenticated ? "Perfil" : "Ingresar" },
            ].map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className="block px-4 py-3 text-gray-600 hover:text-fashion-pink rounded-xl hover:bg-fashion-pink-light transition-all"
                onClick={() => setIsOpen(false)}
              >
                {label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
