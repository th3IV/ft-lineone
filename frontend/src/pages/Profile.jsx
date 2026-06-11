import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { updateMeasurements, updatePreferences } from "../store/userSlice";
import StyleQuiz from "../components/StyleQuiz";

function Profile() {
  const dispatch = useDispatch();
  const { user, isAuthenticated, measurements, preferences } = useSelector((state) => state.user);
  const [editingMeasurements, setEditingMeasurements] = useState(false);
  const [showQuiz, setShowQuiz] = useState(false);
  const [localMeasurements, setLocalMeasurements] = useState(measurements || {});

  useEffect(() => {
    if (measurements) {
      setLocalMeasurements(measurements);
    }
  }, [measurements]);

  const handleSaveMeasurements = () => {
    dispatch(updateMeasurements(localMeasurements));
    setEditingMeasurements(false);
  };

  const handleQuizComplete = (prefs) => {
    dispatch(updatePreferences(prefs));
    setShowQuiz(false);
  };

  const tryOnHistory = JSON.parse(localStorage.getItem("tryOnHistory") || "[]");

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Sign In Required</h1>
        <p className="text-gray-600">Please sign in to view your profile.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Profile</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Personal Info</h2>
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500">Name</span>
                <p className="text-gray-900 font-medium">{user?.name || "N/A"}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Email</span>
                <p className="text-gray-900 font-medium">{user?.email || "N/A"}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Body Measurements</h2>
              <button
                onClick={() => setEditingMeasurements(!editingMeasurements)}
                className="text-sm text-indigo-600 hover:text-indigo-700"
              >
                {editingMeasurements ? "Cancel" : "Edit"}
              </button>
            </div>
            {editingMeasurements ? (
              <div className="space-y-4">
                {["height", "weight", "chest", "waist", "hips", "inseam"].map((field) => (
                  <div key={field}>
                    <label className="block text-sm text-gray-600 capitalize mb-1">{field}</label>
                    <input
                      type="text"
                      value={localMeasurements[field] || ""}
                      onChange={(e) =>
                        setLocalMeasurements({ ...localMeasurements, [field]: e.target.value })
                      }
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      placeholder={field}
                    />
                  </div>
                ))}
                <button
                  onClick={handleSaveMeasurements}
                  className="bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
                >
                  Save
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {Object.entries(measurements || {}).map(([key, value]) => (
                  <div key={key}>
                    <span className="text-sm text-gray-500 capitalize block">{key}</span>
                    <span className="text-gray-900 font-medium">{value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Style Preferences</h2>
              <button
                onClick={() => setShowQuiz(!showQuiz)}
                className="text-sm text-indigo-600 hover:text-indigo-700"
              >
                {showQuiz ? "Cancel" : preferences ? "Update" : "Take Quiz"}
              </button>
            </div>
            {showQuiz ? (
              <StyleQuiz onComplete={handleQuizComplete} initialPreferences={preferences} />
            ) : preferences ? (
              <div className="flex flex-wrap gap-2">
                {Object.entries(preferences).map(([key, value]) => (
                  <span
                    key={key}
                    className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full text-sm"
                  >
                    {key}: {value}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No preferences set yet.</p>
            )}
          </div>
        </div>

        <div className="space-y-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Try-On History</h2>
            {tryOnHistory.length > 0 ? (
              <div className="grid grid-cols-2 gap-2">
                {tryOnHistory.map((entry) => (
                  <div key={entry.id} className="aspect-square rounded-lg overflow-hidden bg-gray-100">
                    <img
                      src={entry.resultImage}
                      alt={entry.productName}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No try-ons yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
