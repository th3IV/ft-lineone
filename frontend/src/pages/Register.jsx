import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { registerUser, clearError } from "../store/userSlice";

function Register() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isAuthenticated, loading, error } = useSelector((state) => state.user);

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    dispatch(clearError());
  }, [dispatch]);

  useEffect(() => {
    if (isAuthenticated) {
      toast.success("Registro exitoso! Bienvenido!");
      navigate("/");
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (error) {
      toast.error(typeof error === "string" ? error : "Error al registrarse");
    }
  }, [error]);

  const validate = () => {
    const newErrors = {};
    if (!form.name.trim()) newErrors.name = "El nombre es requerido";
    if (!form.email.trim()) {
      newErrors.email = "El correo es requerido";
    } else if (!/\S+@\S+\.\S+/.test(form.email)) {
      newErrors.email = "Correo inválido";
    }
    if (!form.password) {
      newErrors.password = "La contraseña es requerida";
    } else if (form.password.length < 6) {
      newErrors.password = "Mínimo 6 caracteres";
    }
    if (!form.confirmPassword) {
      newErrors.confirmPassword = "Confirma tu contraseña";
    } else if (form.password !== form.confirmPassword) {
      newErrors.confirmPassword = "Las contraseñas no coinciden";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    dispatch(registerUser({
      name: form.name,
      email: form.email,
      password: form.password,
    }));
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-fashion-pink to-fashion-purple bg-clip-text text-transparent">
            Crear Cuenta
          </h1>
          <p className="text-gray-500 mt-2">Únete a FT. THE LINE ONE</p>
        </div>

        <div className="bg-white rounded-2xl card-shadow p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Nombre Completo
              </label>
              <input
                type="text"
                value={form.name}
                onChange={handleChange("name")}
                placeholder="Tu nombre"
                className={`w-full border rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all bg-white ${
                  errors.name ? "border-red-300 bg-red-50" : "border-gray-200"
                }`}
              />
              {errors.name && (
                <p className="text-red-500 text-xs mt-1">{errors.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Correo Electrónico
              </label>
              <input
                type="email"
                value={form.email}
                onChange={handleChange("email")}
                placeholder="correo@ejemplo.com"
                className={`w-full border rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all bg-white ${
                  errors.email ? "border-red-300 bg-red-50" : "border-gray-200"
                }`}
              />
              {errors.email && (
                <p className="text-red-500 text-xs mt-1">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Contraseña
              </label>
              <input
                type="password"
                value={form.password}
                onChange={handleChange("password")}
                placeholder="Mínimo 6 caracteres"
                className={`w-full border rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all bg-white ${
                  errors.password ? "border-red-300 bg-red-50" : "border-gray-200"
                }`}
              />
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">{errors.password}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Confirmar Contraseña
              </label>
              <input
                type="password"
                value={form.confirmPassword}
                onChange={handleChange("confirmPassword")}
                placeholder="Repite tu contraseña"
                className={`w-full border rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all bg-white ${
                  errors.confirmPassword ? "border-red-300 bg-red-50" : "border-gray-200"
                }`}
              />
              {errors.confirmPassword && (
                <p className="text-red-500 text-xs mt-1">{errors.confirmPassword}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary text-base py-3 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center gap-2 justify-center">
                  <span className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  Creando cuenta...
                </span>
              ) : (
                "Crear Cuenta"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              ¿Ya tienes cuenta?{" "}
              <Link to="/login" className="text-fashion-pink font-semibold hover:text-fashion-purple transition-colors">
                Inicia sesión
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register;
