import { useState } from "react";

const questions = [
  {
    id: "style",
    question: "How would you describe your style?",
    options: ["Casual", "Formal", "Sporty", "Bohemian", "Minimalist", "Trendy"],
  },
  {
    id: "colors",
    question: "Which colors do you prefer?",
    options: ["Neutrals", "Pastels", "Bold & Bright", "Dark & Moody", "Earth Tones", "All Colors"],
  },
  {
    id: "occasions",
    question: "What occasions do you dress for most?",
    options: ["Work", "Casual Outings", "Party & Nightlife", "Sports & Gym", "Formal Events", "Everyday"],
  },
  {
    id: "fit",
    question: "What fit do you prefer?",
    options: ["Slim Fit", "Regular Fit", "Loose Fit", "Oversized", "Tailored"],
  },
  {
    id: "budget",
    question: "What's your typical budget per item?",
    options: ["Under $25", "$25-$50", "$50-$100", "$100-$200", "$200+"],
  },
];

function StyleQuiz({ onComplete, initialPreferences }) {
  const [step, setStep] = useState(0);
  const [preferences, setPreferences] = useState(initialPreferences || {});

  const handleSelect = (option) => {
    const current = questions[step];
    const updated = { ...preferences, [current.id]: option };
    setPreferences(updated);

    if (step < questions.length - 1) {
      setStep(step + 1);
    } else {
      onComplete(updated);
    }
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  const current = questions[step];
  const progress = ((step + 1) / questions.length) * 100;

  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="mb-6">
        <div className="flex justify-between text-xs text-editorial-gray mb-2">
          <span>Pregunta {step + 1} de {questions.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-editorial-black/5 rounded-full h-1">
          <div
            className="bg-editorial-black h-1 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="bg-editorial-white rounded-2xl p-6">
        <h3 className="text-base font-display font-semibold text-editorial-black mb-4">
          {current.question}
        </h3>
        <div className="space-y-2">
          {current.options.map((option) => (
            <button
              key={option}
              onClick={() => handleSelect(option)}
              className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-all duration-200 ${
                preferences[current.id] === option
                  ? "border-editorial-black bg-editorial-black text-white"
                  : "border-editorial-black/10 text-editorial-gray hover:border-editorial-black/30"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
        {step > 0 && (
          <button
            onClick={handleBack}
            className="mt-4 text-xs text-editorial-gray hover:text-editorial-black transition-colors"
          >
            Volver
          </button>
        )}
      </div>
    </div>
  );
}

export default StyleQuiz;
