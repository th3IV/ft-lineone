import { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, User, LogOut, Settings, Crown, Sparkles } from "lucide-react";
import { useFeatureGate } from "../hooks/useFeatureGate";
import { loginUser, logoutUser } from "../store/userSlice";

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [scrolled, setScrolled] = useState(false);
  const menuRef = useRef(null);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, isAuthenticated, loading, error, profileStatus } = useSelector(
    (state) => state.user
  );
  const { isPremium, isUnlimited, vtonRemaining, llmRemaining, limit } = useFeatureGate();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

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
        const quizDone = res.payload?.user?.preferences?.quiz_completed;
        navigate(quizDone ? "/catalog" : "/onboarding");
      }
    });
  };

  const handleLogout = () => {
    dispatch(logoutUser());
    setUserMenuOpen(false);
    navigate("/");
  };

  const navLinks = [
    { to: "/catalog", label: "Catalogo" },
    { to: "/virtual-try-on", label: "Try-On IA" },
  ];

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled
            ? "bg-editorial-cream/95 backdrop-blur-xl shadow-[0_1px_0_rgba(0,0,0,0.05)]"
            : "bg-editorial-cream/60 backdrop-blur-md"
        }`}
      >
        <div className="max-w-[1400px] mx-auto px-5 sm:px-8">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <img
                src="/logo.jpg"
                alt="FT. THE LINE ONE"
                className="w-8 h-8 rounded-full object-cover"
              />
              <span className="text-[15px] font-display italic font-semibold tracking-[0.15em] text-editorial-black">
                FT. THE LINE ONE
              </span>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  className="relative px-4 py-2 text-[13px] font-medium text-editorial-gray hover:text-editorial-black tracking-wide transition-colors duration-200 group"
                >
                  {label}
                  <span className="absolute bottom-0 left-4 right-4 h-[1px] bg-editorial-black scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                </Link>
              ))}

              {/* User Menu */}
              <div className="relative ml-3" ref={menuRef}>
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-full hover:bg-editorial-black/5 transition-all duration-200"
                >
                  {profileStatus === "loading" ? (
                    <span className="w-7 h-7 rounded-full flex items-center justify-center bg-editorial-black/10">
                      <span className="w-3 h-3 rounded-full border-2 border-editorial-black/20 border-t-editorial-black/60 animate-spin" />
                    </span>
                  ) : isAuthenticated && user?.name ? (
                    <span className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold ${isPremium ? 'bg-editorial-gold text-white' : 'bg-editorial-black text-white'}`}>
                      {isPremium ? <Crown size={12} /> : user.name.charAt(0).toUpperCase()}
                    </span>
                  ) : isAuthenticated ? (
                    <span className="w-7 h-7 rounded-full flex items-center justify-center bg-editorial-black/10">
                      <span className="w-3 h-3 rounded-full border-2 border-editorial-black/20 border-t-editorial-black/60 animate-spin" />
                    </span>
                  ) : (
                    <User size={18} className="text-editorial-gray" />
                  )}
                </button>

                <AnimatePresence>
                  {userMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, scale: 0.96 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 8, scale: 0.96 }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                      className="absolute right-0 mt-2 w-72 bg-editorial-white rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.12)] border border-editorial-black/5 overflow-hidden"
                    >
                      {isAuthenticated ? (
                        <div className="p-5">
                          <div className="flex items-center gap-3 mb-4 pb-4 border-b border-editorial-black/5">
                            <span className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold ${isPremium ? 'bg-editorial-gold text-white' : 'bg-editorial-black text-white'}`}>
                              {isPremium ? <Crown size={16} /> : (user?.name?.charAt(0).toUpperCase() || "U")}
                            </span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-semibold text-editorial-black truncate">
                                  {user?.name || "Usuario"}
                                </p>
                                {isPremium && (
                                  <span className="text-[9px] font-bold uppercase tracking-wider bg-editorial-gold text-white px-1.5 py-0.5 rounded-full">
                                    Premium
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-editorial-gray truncate">
                                {user?.email || ""}
                              </p>
                            </div>
                          </div>

                          {!isUnlimited && (
                            <div className="mb-4 space-y-1.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-editorial-gray">VTON hoy</span>
                                <span className={`font-medium ${vtonRemaining <= 3 ? 'text-red-500' : 'text-editorial-black'}`}>
                                  {vtonRemaining}/{limit} restantes
                                </span>
                              </div>
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-editorial-gray">Chat IA hoy</span>
                                <span className={`font-medium ${llmRemaining <= 3 ? 'text-red-500' : 'text-editorial-black'}`}>
                                  {llmRemaining}/{limit} restantes
                                </span>
                              </div>
                            </div>
                          )}
                          {isUnlimited && (
                            <div className="mb-4 flex items-center gap-2 text-xs text-editorial-gold font-medium">
                              <Crown size={12} />
                              Uso ilimitado
                            </div>
                          )}

                          <Link
                            to="/profile"
                            onClick={() => setUserMenuOpen(false)}
                            className="flex items-center gap-3 w-full px-4 py-2.5 text-sm font-medium text-editorial-black rounded-xl hover:bg-editorial-cream transition-all mb-1"
                          >
                            <Settings size={16} />
                            Mi Perfil
                          </Link>
                          <button
                            onClick={handleLogout}
                            className="flex items-center gap-3 w-full px-4 py-2.5 text-sm font-medium text-editorial-gray rounded-xl hover:bg-editorial-cream hover:text-editorial-black transition-all"
                          >
                            <LogOut size={16} />
                            Cerrar sesion
                          </button>
                        </div>
                      ) : (
                        <form onSubmit={handleLogin} className="p-5 space-y-4">
                          <div className="text-center">
                            <h3 className="text-base font-display font-semibold text-editorial-black">
                              Iniciar Sesion
                            </h3>
                          </div>
                          <div>
                            <input
                              type="email"
                              value={email}
                              onChange={(e) => setEmail(e.target.value)}
                              placeholder="Email"
                              required
                              className="w-full border-b border-editorial-black/10 rounded-none px-0 py-2.5 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
                            />
                          </div>
                          <div>
                            <input
                              type="password"
                              value={password}
                              onChange={(e) => setPassword(e.target.value)}
                              placeholder="Contrasena"
                              required
                              className="w-full border-b border-editorial-black/10 rounded-none px-0 py-2.5 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
                            />
                          </div>
                          {error && (
                            <p className="text-xs text-red-500 text-center">
                              {error}
                            </p>
                          )}
                          <button
                            type="submit"
                            disabled={loading}
                            className="w-full btn-primary disabled:opacity-60 flex items-center justify-center gap-2"
                          >
                            {loading ? (
                              <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                            ) : (
                              "Ingresar"
                            )}
                          </button>
                          <p className="text-xs text-center text-editorial-gray">
                            No tienes cuenta?{" "}
                            <Link
                              to="/register"
                              className="text-editorial-black font-medium hover:underline"
                              onClick={() => setUserMenuOpen(false)}
                            >
                              Registrate
                            </Link>
                          </p>
                        </form>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden p-2 rounded-lg text-editorial-gray hover:text-editorial-black hover:bg-editorial-black/5 transition-all"
            >
              {isOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, x: "100%" }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed inset-0 z-[60] bg-editorial-black md:hidden"
          >
            <div className="flex flex-col h-full pt-20 px-8">
              <button
                onClick={() => setIsOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-lg text-white/60 hover:text-white"
              >
                <X size={22} />
              </button>

              <div className="space-y-1">
                {navLinks.map(({ to, label }, i) => (
                  <motion.div
                    key={to}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                  >
                    <Link
                      to={to}
                      className="block py-4 text-2xl font-display text-white transition-colors"
                      onClick={() => setIsOpen(false)}
                    >
                      {label}
                    </Link>
                  </motion.div>
                ))}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <Link
                    to={isAuthenticated ? "/profile" : "/login"}
                    className="block py-4 text-2xl font-display text-white transition-colors"
                    onClick={() => setIsOpen(false)}
                  >
                    {isAuthenticated ? "Perfil" : "Ingresar"}
                  </Link>
                </motion.div>
              </div>

              {isAuthenticated && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="mt-auto mb-12"
                >
                  <Link
                    to="/virtual-try-on"
                    className="btn-gradient w-full flex items-center justify-center gap-2"
                    onClick={() => setIsOpen(false)}
                  >
                    <Sparkles size={16} />
                    Probar con IA
                  </Link>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default Navbar;
