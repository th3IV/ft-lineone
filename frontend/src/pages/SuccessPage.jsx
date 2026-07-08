import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle, Crown, ArrowLeft } from "lucide-react";
import { useDispatch } from "react-redux";
import { fetchProfile } from "../store/userSlice";

function SuccessPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const dispatch = useDispatch();
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      return;
    }

    // Poll for status update
    const checkPayment = async () => {
      try {
        await dispatch(fetchProfile());
        setStatus("success");
      } catch {
        setStatus("error");
      }
    };

    const timer = setTimeout(checkPayment, 2000);
    return () => clearTimeout(timer);
  }, [searchParams, dispatch]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen flex items-center justify-center px-4"
    >
      <div className="max-w-md w-full text-center">
        {status === "loading" && (
          <>
            <div className="w-16 h-16 mx-auto mb-6 rounded-full border-4 border-editorial-gray-light border-t-editorial-black animate-spin" />
            <h1 className="text-2xl font-display font-bold text-editorial-black mb-2">
              Procesando...
            </h1>
            <p className="text-editorial-gray">
              Verificando tu pago
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 200, damping: 15 }}
            >
              <CheckCircle size={64} className="mx-auto text-green-500 mb-6" />
            </motion.div>
            <h1 className="text-2xl font-display font-bold text-editorial-black mb-2">
              ¡Bienvenido a Premium!
            </h1>
            <p className="text-editorial-gray mb-6">
              Tu suscripción está activa. Disfruta de pruebas ilimitadas y recomendaciones exclusivas.
            </p>
            <div className="flex items-center justify-center gap-2 mb-8 text-amber-600">
              <Crown size={20} />
              <span className="font-medium">Plan Premium Activo</span>
            </div>
            <button
              onClick={() => navigate("/profile")}
              className="btn-primary w-full"
            >
              Volver a mi perfil
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <h1 className="text-2xl font-display font-bold text-editorial-black mb-2">
              Algo salió mal
            </h1>
            <p className="text-editorial-gray mb-6">
              No pudimos verificar tu pago. Por favor contacta soporte.
            </p>
            <button
              onClick={() => navigate("/profile")}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <ArrowLeft size={16} />
              Volver al perfil
            </button>
          </>
        )}
      </div>
    </motion.div>
  );
}

export default SuccessPage;
