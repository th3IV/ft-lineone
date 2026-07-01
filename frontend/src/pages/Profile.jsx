import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { updateMeasurements, updatePreferences } from "../store/userSlice";
import api from "../services/api";

const colorPalettes = [
  { name: "Neutros", colors: ["#1a1a1a", "#6b7280", "#d1d5db", "#f3f4f6", "#faf8f5"] },
  { name: "Pasteles", colors: ["#fbcfe8", "#bfdbfe", "#c7d2fe", "#fde68a", "#a7f3d0"] },
  { name: "Vibrantes", colors: ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"] },
  { name: "Oscuros", colors: ["#0f0f0f", "#1f2937", "#374151", "#4b5563", "#6b7280"] },
  { name: "Tierra", colors: ["#8b5cf6", "#a78bfa", "#c4b5fd", "#f5f3ff", "#ede9fe"] },
];

const styleOptions = ["Casual", "Formal", "Deportivo", "Bohemio", "Minimalista", "Trendy"];

function Profile() {
  const dispatch = useDispatch();
  const { user, isAuthenticated, measurements, preferences, loading } = useSelector((state) => state.user);
  const [editingPersonal, setEditingPersonal] = useState(false);
  const [editingMeasurements, setEditingMeasurements] = useState(false);
  const [localUser, setLocalUser] = useState({ name: "", email: "" });
  const [localMeasurements, setLocalMeasurements] = useState(measurements || {});
  const [localPreferences, setLocalPreferences] = useState(preferences || {});
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (user) {
      setLocalUser({ name: user.name || "", email: user.email || "" });
    }
    if (measurements) {
      setLocalMeasurements(measurements);
    }
    if (preferences) {
      setLocalPreferences(preferences);
    }
  }, [user, measurements, preferences]);

  const handleSavePersonal = async () => {
    setSaving(true);
    try {
      await api.put("/user/profile", localUser);
      setEditingPersonal(false);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMeasurements = () => {
    dispatch(updateMeasurements(localMeasurements));
    setEditingMeasurements(false);
  };

  const handleSavePreferences = () => {
    dispatch(updatePreferences(localPreferences));
  };

  const togglePreference = (key, value) => {
    setLocalPreferences((prev) => ({
      ...prev,
      [key]: prev[key] === value ? "" : value,
    }));
  };

  const tryOnHistory = (() => {
    try {
      return JSON.parse(localStorage.getItem("tryOnHistory") || "[]");
    } catch {
      return [];
    }
  })();

  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Inicia Sesión</h1>
        <p className="text-gray-500">Necesitas iniciar sesión para ver tu perfil.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center gap-4 mb-8">
        <span className="w-14 h-14 rounded-full bg-gradient-to-br from-fashion-pink to-fashion-purple text-white flex items-center justify-center text-xl font-bold">
          {user?.name?.charAt(0).toUpperCase() || "U"}
        </span>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mi Perfil</h1>
          <p className="text-sm text-gray-500">Gestiona tu información personal y preferencias</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Personal Info */}
          <section className="bg-white rounded-xl card-shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Información Personal</h2>
              <button
                onClick={() => setEditingPersonal(!editingPersonal)}
                className={`text-sm font-medium transition-all ${
                  editingPersonal ? "text-gray-500 hover:text-gray-700" : "text-fashion-pink hover:text-fashion-purple"
                }`}
              >
                {editingPersonal ? "Cancelar" : "Editar"}
              </button>
            </div>
            {editingPersonal ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Nombre</label>
                  <input
                    type="text"
                    value={localUser.name}
                    onChange={(e) => setLocalUser({ ...localUser, name: e.target.value })}
                    className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input
                    type="email"
                    value={localUser.email}
                    onChange={(e) => setLocalUser({ ...localUser, email: e.target.value })}
                    className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all"
                  />
                </div>
                <button
                  onClick={handleSavePersonal}
                  disabled={saving}
                  className="btn-primary text-sm !py-2.5 !px-6"
                >
                  {saving ? "Guardando..." : "Guardar"}
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-fashion-pink-light flex items-center justify-center">
                    <svg className="w-4 h-4 text-fashion-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </span>
                  <div>
                    <p className="text-sm text-gray-500">Nombre</p>
                    <p className="text-gray-900 font-medium">{user?.name || "—"}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-fashion-pink-light flex items-center justify-center">
                    <svg className="w-4 h-4 text-fashion-pink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </span>
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="text-gray-900 font-medium">{user?.email || "—"}</p>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Body Measurements */}
          <section className="bg-white rounded-xl card-shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Medidas Corporales</h2>
              <button
                onClick={() => setEditingMeasurements(!editingMeasurements)}
                className={`text-sm font-medium transition-all ${
                  editingMeasurements ? "text-gray-500 hover:text-gray-700" : "text-fashion-pink hover:text-fashion-purple"
                }`}
              >
                {editingMeasurements ? "Cancelar" : "Editar"}
              </button>
            </div>
            {editingMeasurements ? (
              <div className="grid grid-cols-2 gap-4">
                {["height", "weight", "chest", "waist", "hips", "inseam"].map((field) => (
                  <div key={field}>
                    <label className="block text-xs font-medium text-gray-600 capitalize mb-1">{field}</label>
                    <input
                      type="text"
                      value={localMeasurements[field] || ""}
                      onChange={(e) =>
                        setLocalMeasurements({ ...localMeasurements, [field]: e.target.value })
                      }
                      className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-fashion-pink focus:border-transparent transition-all"
                      placeholder={field}
                    />
                  </div>
                ))}
                <div className="col-span-2">
                  <button
                    onClick={handleSaveMeasurements}
                    className="btn-primary text-sm !py-2.5 !px-6"
                  >
                    Guardar Medidas
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {Object.entries(measurements || {}).length > 0 ? (
                  Object.entries(measurements).map(([key, value]) => (
                    <div key={key} className="bg-gray-50 rounded-xl p-3">
                      <span className="text-xs text-gray-500 capitalize block">{key}</span>
                      <span className="text-gray-900 font-semibold">{value}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-sm col-span-full">Sin medidas registradas.</p>
                )}
              </div>
            )}
          </section>

          {/* Style Preferences */}
          <section className="bg-white rounded-xl card-shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Gustos y Preferencias</h2>
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">Paleta de Colores</h4>
                <div className="flex flex-wrap gap-3">
                  {colorPalettes.map((palette) => (
                    <button
                      key={palette.name}
                      onClick={() => togglePreference("colors", palette.name)}
                      className={`px-4 py-2.5 rounded-xl border-2 transition-all ${
                        localPreferences.colors === palette.name
                          ? "border-fashion-pink ring-2 ring-fashion-pink/20 bg-fashion-pink-light"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                    >
                      <div className="flex gap-1 mb-1">
                        {palette.colors.map((c, i) => (
                          <span key={i} className="w-4 h-4 rounded-full" style={{ backgroundColor: c }} />
                        ))}
                      </div>
                      <span className={`text-xs font-medium ${localPreferences.colors === palette.name ? "text-fashion-pink" : "text-gray-600"}`}>
                        {palette.name}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">Estilos</h4>
                <div className="flex flex-wrap gap-2">
                  {styleOptions.map((style) => (
                    <button
                      key={style}
                      onClick={() => togglePreference("style", style)}
                      className={`tag-pill ${
                        localPreferences.style === style
                          ? "bg-fashion-pink text-white border-fashion-pink"
                          : "bg-white text-gray-600 border-gray-200 hover:border-fashion-pink"
                      }`}
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">Ocasiones / Fit / Presupuesto</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { key: "occasions", label: "Ocasión", options: ["Diario", "Fiesta", "Trabajo", "Deporte"] },
                    { key: "fit", label: "Fit", options: ["Ajustado", "Regular", "Holgado"] },
                    { key: "budget", label: "Presupuesto", options: ["Económico", "Medio", "Premium"] },
                  ].map((group) => (
                    <div key={group.key}>
                      <p className="text-xs text-gray-500 mb-2 font-medium">{group.label}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {group.options.map((opt) => (
                          <button
                            key={opt}
                            onClick={() => togglePreference(group.key, opt)}
                            className={`text-xs px-2.5 py-1.5 rounded-lg border transition-all ${
                              localPreferences[group.key] === opt
                                ? "bg-fashion-pink text-white border-fashion-pink"
                                : "bg-white text-gray-600 border-gray-200 hover:border-fashion-pink"
                            }`}
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={handleSavePreferences}
                disabled={loading}
                className="btn-primary text-sm !py-2.5 !px-6"
              >
                {loading ? "Guardando..." : "Guardar Preferencias"}
              </button>
            </div>
          </section>
        </div>

        <div className="space-y-8">
          {/* Try-On History */}
          <section className="bg-white rounded-xl card-shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Historial de Try-On</h2>
            {tryOnHistory.length > 0 ? (
              <div className="grid grid-cols-2 gap-2">
                {tryOnHistory.map((entry) => (
                  <div key={entry.id} className="aspect-square rounded-xl overflow-hidden bg-gray-100">
                    <img
                      src={entry.resultImage}
                      alt={entry.productName}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <svg className="w-10 h-10 mx-auto text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="text-sm text-gray-400">Sin try-ons aún.</p>
                <p className="text-xs text-gray-300 mt-1">Prueba prendas desde el catálogo.</p>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

export default Profile;
