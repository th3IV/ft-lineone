import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle, Crown, ArrowLeft, XCircle } from "lucide-react";
import { useDispatch } from "react-redux";
import { fetchProfile } from "../store/userSlice";
import api from "../services/api";

function SuccessPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const dispatch = useDispatch();
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    const tokenWs = searchParams.get("token_ws");
    const tbkToken = searchParams.get("TBK_TOKEN");

    // User cancelled or timed out
    if (!tokenWs && tbkToken) {
      setStatus("cancelled");
      return;
    }

    if (!tokenWs) {
      setStatus("error");
      return;
    }

    const confirmPayment = async () => {
      try {
        const result = await api.post("/payments/confirm", { token: tokenWs });

        if (result.data?.status === "success") {
          await dispatch(fetchProfile());
          setStatus("success");
        } else {
          setStatus("error");
        }
      } catch {
        setStatus("error");
      }
    };

    confirmPayment();
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

        {status === "cancelled" && (
          <>
            <h1 className="text-2xl font-display font-bold text-editorial-black mb-2">
              Pago cancelado
            </h1>
            <p className="text-editorial-gray mb-6">
              No se realizó ningún cobro. Puedes intentar nuevamente cuando quieras.
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
