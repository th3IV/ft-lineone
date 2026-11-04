import { motion } from "framer-motion";

function HypnoticLoader({ variant = "processing", className = "" }) {
  const label =
    variant === "uploading"
      ? "Preparando tu imagen..."
      : variant === "generating"
      ? "Generando tu look..."
      : "Procesando...";

  return (
    <div className={`flex flex-col items-center justify-center gap-6 ${className}`}>
      {/* Orbital rings */}
      <div className="relative w-28 h-28">
        {/* Outer ring */}
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-editorial-black/5"
          style={{
            borderTopColor: "var(--color-editorial-black, #0a0a0a)",
            borderRightColor: "transparent",
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />

        {/* Middle ring */}
        <motion.div
          className="absolute inset-2 rounded-full border-2 border-editorial-black/5"
          style={{
            borderBottomColor: "var(--color-editorial-black, #0a0a0a)",
            borderLeftColor: "transparent",
          }}
          animate={{ rotate: -360 }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        />

        {/* Inner ring */}
        <motion.div
          className="absolute inset-4 rounded-full border-2 border-editorial-black/5"
          style={{
            borderTopColor: "var(--color-editorial-black, #0a0a0a)",
            borderRightColor: "transparent",
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
        />

        {/* Center pulsing dot */}
        <motion.div
          className="absolute inset-0 flex items-center justify-center"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className="w-3 h-3 rounded-full bg-editorial-black/80" />
        </motion.div>

        {/* Orbiting particles */}
        {[0, 1, 2, 3].map((i) => (
          <motion.div
            key={i}
            className="absolute w-1.5 h-1.5 rounded-full bg-editorial-black/30"
            style={{
              top: "50%",
              left: "50%",
              marginTop: -3,
              marginLeft: -3,
            }}
            animate={{
              rotate: 360,
              x: [
                Math.cos((i * Math.PI) / 2) * 40,
                Math.cos((i * Math.PI) / 2 + Math.PI * 2) * 40,
              ],
              y: [
                Math.sin((i * Math.PI) / 2) * 40,
                Math.sin((i * Math.PI) / 2 + Math.PI * 2) * 40,
              ],
            }}
            transition={{
              duration: 2.5 + i * 0.3,
              repeat: Infinity,
              ease: "linear",
            }}
          />
        ))}
      </div>

      {/* Label */}
      <motion.p
        className="text-xs text-editorial-gray font-medium tracking-wide"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        {label}
      </motion.p>
    </div>
  );
}

export default HypnoticLoader;
