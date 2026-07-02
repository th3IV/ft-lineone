module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        fashion: {
          pink: "#ec4899",
          "pink-light": "#fdf2f8",
          purple: "#7c3aed",
          "purple-light": "#f5f3ff",
          amber: "#f59e0b",
          "amber-light": "#fffbeb",
        },
        editorial: {
          black: "#0a0a0a",
          charcoal: "#1a1a2e",
          gray: "#6b7280",
          "gray-light": "#9ca3af",
          cream: "#faf8f5",
          "cream-dark": "#f5f0eb",
          white: "#ffffff",
          gold: "#b8860b",
          "gold-soft": "#fef9e7",
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.6s ease-out forwards",
        "slide-up": "slideUp 0.6s ease-out forwards",
        "slide-in-left": "slideInLeft 0.4s ease-out forwards",
        "slide-in-right": "slideInRight 0.4s ease-out forwards",
        "bounce-in": "bounceIn 0.5s ease-out forwards",
        "scale-in": "scaleIn 0.3s ease-out forwards",
        "underline-expand": "underlineExpand 0.3s ease-out forwards",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(30px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        bounceIn: {
          "0%": { opacity: "0", transform: "scale(0.9)" },
          "50%": { transform: "scale(1.05)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        underlineExpand: {
          "0%": { transform: "scaleX(0)" },
          "100%": { transform: "scaleX(1)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};
