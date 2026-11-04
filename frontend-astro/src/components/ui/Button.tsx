import { forwardRef, ButtonHTMLAttributes } from "react";
import { motion } from "framer-motion";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, variant = "primary", size = "md", loading = false, className = "", disabled, ...props }, ref) => {
    const baseStyles = `
      inline-flex items-center justify-center font-display font-medium
      transition-all duration-300 ease-out
      focus:outline-none focus-visible:ring-2 focus-visible:ring-editorial-gold focus-visible:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
      select-none
    `;

    const variants = {
      primary: "bg-editorial-black text-editorial-white hover:bg-editorial-gold hover:text-editorial-black",
      secondary: "bg-transparent text-editorial-black border border-editorial-black hover:bg-editorial-black hover:text-editorial-white",
      outline: "bg-transparent text-editorial-black border border-editorial-gray hover:bg-editorial-cream-dark",
      ghost: "text-editorial-black hover:text-editorial-gold hover:bg-editorial-cream",
    };

    const sizes = {
      sm: "px-4 py-2 text-xs",
      md: "px-6 py-3 text-sm",
      lg: "px-8 py-4 text-base",
    };

    return (
      <motion.button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        whileTap={{ scale: 0.98 }}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Cargando...</span>
          </span>
        ) : (
          children
        )}
      </motion.button>
    );
  }
);

Button.displayName = "Button";