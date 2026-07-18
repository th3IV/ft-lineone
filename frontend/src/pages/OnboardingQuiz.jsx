import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { updatePreferences, updateMeasurements } from "../store/userSlice";

const STEPS = [
  {
    id: "occasions",
    title: "¿A donde iras esta semana?",
    subtitle: "Selecciona las ocasiones mas comunes",
    type: "multi",
    options: [
      { value: "oficina", label: "Oficina" },
      { value: "cafe", label: "Cafe / Reunión" },
      { value: "fiesta", label: "Fiesta / Noche" },
      { value: "gym", label: "Gimnasio / Deporte" },
      { value: "paseo", label: "Paseo / Casual" },
      { value: "formal", label: "Evento formal" },
    ],
  },
  {
    id: "colors",
    title: "¿Que colores te hacen sentir bien?",
    subtitle: "Elige tus favoritos",
    type: "colors",
    options: [
      { value: "negro", label: "Negro", hex: "#000000" },
      { value: "blanco", label: "Blanco", hex: "#FFFFFF" },
      { value: "gris", label: "Gris", hex: "#9CA3AF" },
      { value: "azul", label: "Azul", hex: "#3B82F6" },
      { value: "beige", label: "Beige", hex: "#D4C5A9" },
      { value: "marron", label: "Marrón", hex: "#92400E" },
      { value: "verde", label: "Verde", hex: "#22C55E" },
      { value: "rosa", label: "Rosa", hex: "#F472B6" },
    ],
  },
  {
    id: "styles",
    title: "¿Como te describirias?",
    subtitle: "Selecciona los estilos que mas te representan",
    type: "multi",
    options: [
      { value: "minimalista", label: "Minimalista" },
      { value: "streetwear", label: "Urbano / Street" },
      { value: "casual", label: "Relajado" },
      { value: "formal", label: "Elegante" },
      { value: "bohemio", label: "Bohemio" },
      { value: "deportivo", label: "Deportivo" },
    ],
  },
  {
    id: "avoided_colors",
    title: "¿Hay colores que NO uses?",
    subtitle: "Los evitaremos en tus recomendaciones",
    type: "colors",
    options: [
      { value: "negro", label: "Negro", hex: "#000000" },
      { value: "blanco", label: "Blanco", hex: "#FFFFFF" },
      { value: "gris", label: "Gris", hex: "#9CA3AF" },
      { value: "azul", label: "Azul", hex: "#3B82F6" },
      { value: "beige", label: "Beige", hex: "#D4C5A9" },
      { value: "marron", label: "Marron", hex: "#92400E" },
      { value: "verde", label: "Verde", hex: "#22C55E" },
      { value: "rosa", label: "Rosa", hex: "#F472B6" },
    ],
  },
  {
    id: "measurements",
    title: "Tus medidas (opcional)",
    subtitle: "Ayudanos a recomendarte la talla perfecta",
    type: "measurements",
  },
];

function OnboardingQuiz() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user } = useSelector((state) => state.user);
  const [step, setStep] = useState(0);
  const [selections, setSelections] = useState({
    occasions: [],
    colors: [],
    avoided_colors: [],
    styles: [],
    measurements: {
      height: "",
      weight: "",
      chest: "",
      waist: "",
      hips: "",
      bodyShape: "",
    },
  });

  const currentStep = STEPS[step];
  const isLast = step === STEPS.length - 1;

  const toggleMulti = (field, value) => {
    setSelections((prev) => {
      const arr = prev[field];
      const updated = arr.includes(value)
        ? arr.filter((v) => v !== value)
        : [...arr, value];
      return { ...prev, [field]: updated };
    });
  };

  const handleNext = () => {
    if (isLast) {
      handleComplete();
    } else {
      setStep((s) => s + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) setStep((s) => s - 1);
  };

  const handleComplete = async () => {
    const preferences = {
      quiz_completed: true,
      occasions: selections.occasions,
      colors: selections.colors,
      avoided_colors: selections.avoided_colors,
      styles: selections.styles,
      sizes: user?.preferences?.sizes || { upper: "", lower: "" },
      brands: user?.preferences?.brands || [],
    };

    await dispatch(updatePreferences(preferences));

    const m = selections.measurements;
    if (m.height || m.weight || m.chest || m.waist || m.hips) {
      await dispatch(updateMeasurements(m));
    }

    navigate("/catalog");
  };

  const canProceed = () => {
    if (currentStep.type === "measurements") return true;
    if (currentStep.type === "multi") return selections[currentStep.id]?.length > 0;
    if (currentStep.type === "colors") return selections[currentStep.id]?.length > 0;
    return true;
  };

  return (
    <div className="min-h-screen bg-editorial-cream flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <span className="text-lg font-display italic font-semibold tracking-[0.15em] text-editorial-black">
            FT. THE LINE ONE
          </span>
          <h1 className="text-2xl font-display font-semibold text-editorial-black mt-4">
            Personaliza tu experiencia
          </h1>
          <p className="text-sm text-editorial-gray mt-2">
            Solo toma un minuto. Te ayudara a encontrar prendas que te encanten.
          </p>
        </div>

        {/* Progress */}
        <div className="flex gap-1.5 mb-8">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                i <= step ? "bg-editorial-black" : "bg-editorial-black/10"
              }`}
            />
          ))}
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="min-h-[300px]"
          >
            <h2 className="text-xl font-display font-semibold text-editorial-black mb-2">
              {currentStep.title}
            </h2>
            <p className="text-sm text-editorial-gray mb-6">{currentStep.subtitle}</p>

            {/* Multi Select */}
            {currentStep.type === "multi" && (
              <div className="flex flex-wrap gap-2">
                {currentStep.options.map((opt) => {
                  const selected = selections[currentStep.id]?.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      onClick={() => toggleMulti(currentStep.id, opt.value)}
                      className={`px-4 py-2.5 rounded-full text-sm transition-all duration-200 ${
                        selected
                          ? "bg-editorial-black text-white"
                          : "border border-editorial-black/10 text-editorial-gray hover:border-editorial-black/30"
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Color Select */}
            {currentStep.type === "colors" && (
              <div className="flex flex-wrap gap-3">
                {currentStep.options.map((opt) => {
                  const selected = selections.colors?.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      onClick={() => toggleMulti("colors", opt.value)}
                      className={`w-12 h-12 rounded-full border-2 transition-all duration-200 ${
                        selected
                          ? "border-editorial-black scale-110 ring-2 ring-editorial-black/20"
                          : "border-editorial-gray-light hover:border-editorial-gray"
                      }`}
                      style={{ backgroundColor: opt.hex }}
                      title={opt.label}
                    />
                  );
                })}
              </div>
            )}

            {/* Measurements */}
            {currentStep.type === "measurements" && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { key: "height", label: "Altura (cm)", type: "number" },
                    { key: "weight", label: "Peso (kg)", type: "number" },
                    { key: "chest", label: "Busto (cm)", type: "number" },
                    { key: "waist", label: "Cintura (cm)", type: "number" },
                    { key: "hips", label: "Caderas (cm)", type: "number" },
                  ]
                    .filter((field) => {
                      if (user?.gender === "hombre") {
                        return !["chest", "waist"].includes(field.key);
                      }
                      return true;
                    })
                    .map((field) => (
                    <div key={field.key}>
                      <label className="text-[10px] uppercase tracking-widest text-editorial-gray-light mb-1 block">
                        {field.label}
                      </label>
                      <input
                        type={field.type}
                        value={selections.measurements[field.key] || ""}
                        onChange={(e) =>
                          setSelections((prev) => ({
                            ...prev,
                            measurements: {
                              ...prev.measurements,
                              [field.key]: e.target.value,
                            },
                          }))
                        }
                        className="input-line w-full"
                        placeholder="--"
                      />
                    </div>
                  ))}
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-widest text-editorial-gray-light mb-2 block">
                    Forma del cuerpo
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {["reloj", "pera", "rectangulo", "triangulo", "ovalo"].map((shape) => (
                      <button
                        key={shape}
                        onClick={() =>
                          setSelections((prev) => ({
                            ...prev,
                            measurements: {
                              ...prev.measurements,
                              bodyShape: prev.measurements.bodyShape === shape ? "" : shape,
                            },
                          }))
                        }
                        className={`px-4 py-2 rounded-full text-xs capitalize transition-all ${
                          selections.measurements.bodyShape === shape
                            ? "bg-editorial-black text-white"
                            : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                        }`}
                      >
                        {shape}
                      </button>
                    ))}
                  </div>
                </div>
                <p className="text-[11px] text-editorial-gray-light">
                  Puedes saltar esta parte y completarla despues desde tu perfil.
                </p>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex justify-between items-center mt-8">
          <button
            onClick={handleBack}
            disabled={step === 0}
            className="flex items-center gap-2 text-sm text-editorial-gray hover:text-editorial-black disabled:opacity-30 transition-colors"
          >
            <ArrowLeft size={16} />
            Atras
          </button>

          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {isLast ? (
              <>
                <Check size={16} />
                Completar
              </>
            ) : (
              <>
                Siguiente
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>

        {/* Skip */}
        {!isLast && (
          <button
            onClick={handleComplete}
            className="w-full text-center text-xs text-editorial-gray hover:text-editorial-black mt-4 transition-colors"
          >
            Saltar por ahora
          </button>
        )}
      </motion.div>
    </div>
  );
}

export default OnboardingQuiz;
