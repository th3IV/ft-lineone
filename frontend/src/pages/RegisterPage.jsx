import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { registerUser, clearError } from "../store/userSlice";

function RegisterPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error } = useSelector((state) => state.user);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [gender, setGender] = useState("");
  const [age, setAge] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    dispatch(clearError());
    const payload = { name, email, password };
    if (gender) payload.gender = gender;
    if (age) payload.age = parseInt(age, 10);
    const result = await dispatch(registerUser(payload));
    if (registerUser.fulfilled.match(result)) {
      navigate("/catalog");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-editorial-cream px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-sm"
      >
        <div className="text-center mb-10">
          <Link to="/" className="inline-block mb-6">
            <span className="text-lg font-display italic font-semibold tracking-[0.15em] text-editorial-black">
              FT. THE LINE ONE
            </span>
          </Link>
          <h1 className="text-2xl font-display font-semibold text-editorial-black">
            Crear Cuenta
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 text-red-600 text-xs rounded-xl p-3 text-center">
              {error}
            </div>
          )}

          <div>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full border-b border-editorial-black/10 rounded-none px-0 py-3 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
              placeholder="Nombre"
            />
          </div>

          <div>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full border-b border-editorial-black/10 rounded-none px-0 py-3 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
              placeholder="Email"
            />
          </div>

          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full border-b border-editorial-black/10 rounded-none px-0 py-3 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
              placeholder="Minimo 8 caracteres"
            />
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full border-b border-editorial-black/10 rounded-none px-0 py-3 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors text-editorial-black"
              >
                <option value="">Sexo</option>
                <option value="hombre">Hombre</option>
                <option value="mujer">Mujer</option>
                <option value="unisex">No binario</option>
                <option value="prefiero_no_decir">Prefiero no decir</option>
              </select>
            </div>
            <div className="flex-1">
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                min={13}
                max={120}
                className="w-full border-b border-editorial-black/10 rounded-none px-0 py-3 text-sm bg-transparent focus:outline-none focus:border-editorial-black transition-colors"
                placeholder="Edad"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary disabled:opacity-50"
          >
            {loading ? "Creando cuenta..." : "Crear Cuenta"}
          </button>

          <p className="text-center text-xs text-editorial-gray">
            Ya tienes cuenta?{" "}
            <Link
              to="/login"
              className="text-editorial-black font-medium hover:underline"
            >
              Inicia sesion
            </Link>
          </p>
        </form>
      </motion.div>
    </div>
  );
}

export default RegisterPage;
