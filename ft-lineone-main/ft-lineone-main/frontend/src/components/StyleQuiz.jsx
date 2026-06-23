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
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>Question {step + 1} of {questions.length}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-indigo-600 h-2 rounded-full transition-all" style={{ width: `${progress}%` }}></div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{current.question}</h3>
        <div className="space-y-2">
          {current.options.map((option) => (
            <button
              key={option}
              onClick={() => handleSelect(option)}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                preferences[current.id] === option
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                  : "border-gray-200 hover:border-indigo-300 text-gray-700"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
        {step > 0 && (
          <button
            onClick={handleBack}
            className="mt-4 text-sm text-gray-500 hover:text-gray-700"
          >
            Back
          </button>
        )}
      </div>
    </div>
  );
}

export default StyleQuiz;
