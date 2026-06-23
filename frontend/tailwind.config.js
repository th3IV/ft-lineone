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
          charcoal: "#1a1a2e",
          cream: "#faf8f5",
          navy: "#16213e",
          gold: "#d4a853",
        },
      },
      fontFamily: {
        serif: ['"Playfair Display"', "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "slide-up": "slideUp 0.4s ease-out forwards",
        "slide-in-left": "slideInLeft 0.3s ease-out forwards",
        "bounce-in": "bounceIn 0.5s ease-out forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        bounceIn: {
          "0%": { opacity: "0", transform: "scale(0.9)" },
          "50%": { transform: "scale(1.05)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
    },
  },
  plugins: [],
};
