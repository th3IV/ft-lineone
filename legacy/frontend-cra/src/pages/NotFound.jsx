import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";

function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-editorial-cream px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <h1 className="text-8xl md:text-9xl font-display font-semibold text-editorial-black/10 mb-4">
          404
        </h1>
        <p className="text-editorial-gray text-sm mb-8">
          Pagina no encontrada
        </p>
        <Link
          to="/"
          className="btn-primary inline-flex items-center gap-2"
        >
          <ArrowLeft size={16} />
          Volver al inicio
        </Link>
      </motion.div>
    </div>
  );
}

export default NotFound;
