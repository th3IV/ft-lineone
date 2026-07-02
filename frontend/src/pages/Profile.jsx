import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { User, Settings, Clock, Sparkles, LogOut, Camera } from "lucide-react";
import { fetchProfile, updateProfile, updateMeasurements } from "../store/userSlice";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

const MEASUREMENTS_DEFAULT = {
  height: "",
  weight: "",
  bust: "",
  waist: "",
  hips: "",
  preferredStyle: "",
  bodyShape: "",
  undertone: "",
};

const PREFERENCES_DEFAULT = {
  sizes: { upper: "", lower: "", shoes: "" },
  brands: [],
  colors: [],
  styles: [],
};

function Profile() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, loading } = useSelector((state) => state.user);

  const [profile, setProfile] = useState(user || {});
  const [measurements, setMeasurements] = useState(MEASUREMENTS_DEFAULT);
  const [preferences, setPreferences] = useState(PREFERENCES_DEFAULT);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState("profile");

  useEffect(() => {
    dispatch(fetchProfile());
  }, [dispatch]);

  useEffect(() => {
    if (user) {
      setProfile(user);
      if (user.measurements) setMeasurements(user.measurements);
      if (user.preferences) setPreferences(user.preferences);
    }
  }, [user]);

  const handleSave = async () => {
    await dispatch(updateProfile({ ...profile, measurements, preferences }));
    setIsEditing(false);
  };

  const tabs = [
    { id: "profile", label: "Perfil", icon: User },
    { id: "measurements", label: "Medidas", icon: Settings },
    { id: "preferences", label: "Preferencias", icon: Sparkles },
    { id: "history", label: "Historial", icon: Clock },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="max-w-[1000px] mx-auto px-5 sm:px-8 py-10"
    >
      <h1 className="text-3xl font-display font-bold tracking-tight text-editorial-black mb-8">
        Mi Cuenta
      </h1>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-editorial-gray-light mb-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-3 text-xs uppercase tracking-widest border-b -mb-px transition-colors ${
              activeTab === tab.id
                ? "border-editorial-black text-editorial-black font-medium"
                : "border-transparent text-editorial-gray-light hover:text-editorial-gray"
            }`}
          >
            <tab.icon size={14} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === "profile" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-8"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label className="editorial-label">Nombre</label>
              <input
                type="text"
                value={profile.name || ""}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                disabled={!isEditing}
                className="input-line w-full"
              />
            </div>
            <div>
              <label className="editorial-label">Email</label>
              <input
                type="email"
                value={profile.email || ""}
                disabled
                className="input-line w-full opacity-50"
              />
            </div>
          </div>

          <div>
            <label className="editorial-label">Género</label>
            <div className="flex gap-3 mt-2">
              {["femenino", "masculino", "unisex", "otro"].map((g) => (
                <button
                  key={g}
                  onClick={() => isEditing && setProfile({ ...profile, gender: g })}
                  className={`px-4 py-2 rounded-full text-xs transition-all ${
                    profile.gender === g
                      ? "bg-editorial-black text-white"
                      : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                  } ${!isEditing ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  {g.charAt(0).toUpperCase() + g.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            {isEditing ? (
              <>
                <button
                  onClick={() => setIsEditing(false)}
                  className="btn-outline"
                >
                  Cancelar
                </button>
                <button onClick={handleSave} className="btn-primary">
                  Guardar
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="btn-primary"
              >
                Editar Perfil
              </button>
            )}
          </div>
        </motion.div>
      )}

      {/* Measurements Tab */}
      {activeTab === "measurements" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-8"
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
            {Object.entries({
              height: "Altura (cm)",
              weight: "Peso (kg)",
              bust: "Busto (cm)",
              waist: "Cintura (cm)",
              hips: "Caderas (cm)",
            }).map(([key, label]) => (
              <div key={key}>
                <label className="editorial-label">{label}</label>
                <input
                  type="number"
                  value={measurements[key] || ""}
                  onChange={(e) =>
                    setMeasurements({ ...measurements, [key]: e.target.value })
                  }
                  className="input-line w-full"
                />
              </div>
            ))}
          </div>

          <div>
            <label className="editorial-label">Forma del cuerpo</label>
            <div className="flex gap-3 mt-2 flex-wrap">
              {["reloj", "pera", "rectangulo", "triangulo", "ovalo"].map((shape) => (
                <button
                  key={shape}
                  onClick={() =>
                    setMeasurements({ ...measurements, bodyShape: shape })
                  }
                  className={`px-4 py-2 rounded-full text-xs capitalize transition-all ${
                    measurements.bodyShape === shape
                      ? "bg-editorial-black text-white"
                      : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                  }`}
                >
                  {shape}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={() => dispatch(updateMeasurements(measurements))}
              className="btn-primary"
            >
              Guardar Medidas
            </button>
          </div>
        </motion.div>
      )}

      {/* Preferences Tab */}
      {activeTab === "preferences" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-8"
        >
          <div>
            <label className="editorial-label">Tallas preferidas</label>
            <div className="grid grid-cols-3 gap-4 mt-2">
              {Object.entries({
                upper: "Parte superior",
                lower: "Parte inferior",
                shoes: "Zapatos",
              }).map(([key, label]) => (
                <div key={key}>
                  <span className="text-[10px] uppercase tracking-widest text-editorial-gray-light mb-1 block">
                    {label}
                  </span>
                  <input
                    type="text"
                    value={preferences.sizes?.[key] || ""}
                    onChange={(e) =>
                      setPreferences({
                        ...preferences,
                        sizes: { ...preferences.sizes, [key]: e.target.value },
                      })
                    }
                    className="input-line w-full"
                    placeholder="Ej: S, 38"
                  />
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="editorial-label">Estilos que te gustan</label>
            <div className="flex gap-3 mt-2 flex-wrap">
              {["minimalista", "streetwear", "casual", "formal", "bohemio", "deportivo"].map(
                (style) => (
                  <button
                    key={style}
                    onClick={() => {
                      const styles = preferences.styles || [];
                      const updated = styles.includes(style)
                        ? styles.filter((s) => s !== style)
                        : [...styles, style];
                      setPreferences({ ...preferences, styles: updated });
                    }}
                    className={`px-4 py-2 rounded-full text-xs capitalize transition-all ${
                      preferences.styles?.includes(style)
                        ? "bg-editorial-black text-white"
                        : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                    }`}
                  >
                    {style}
                  </button>
                )
              )}
            </div>
          </div>

          <div>
            <label className="editorial-label">Colores preferidos</label>
            <div className="flex gap-3 mt-2">
              {["negro", "blanco", "gris", "azul", "beige", "marrón", "verde", "rosa"].map(
                (color) => (
                  <button
                    key={color}
                    onClick={() => {
                      const colors = preferences.colors || [];
                      const updated = colors.includes(color)
                        ? colors.filter((c) => c !== color)
                        : [...colors, color];
                      setPreferences({ ...preferences, colors: updated });
                    }}
                    className={`w-8 h-8 rounded-full border-2 transition-all ${
                      preferences.colors?.includes(color)
                        ? "border-editorial-black scale-110"
                        : "border-editorial-gray-light hover:border-editorial-gray"
                    }`}
                    style={{
                      backgroundColor:
                        color === "negro"
                          ? "#000"
                          : color === "blanco"
                          ? "#fff"
                          : color === "gris"
                          ? "#9CA3AF"
                          : color === "azul"
                          ? "#3B82F6"
                          : color === "beige"
                          ? "#D4C5A9"
                          : color === "marrón"
                          ? "#92400E"
                          : color === "verde"
                          ? "#22C55E"
                          : "#F472B6",
                    }}
                  />
                )
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button onClick={handleSave} className="btn-primary">
              Guardar Preferencias
            </button>
          </div>
        </motion.div>
      )}

      {/* History Tab */}
      {activeTab === "history" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="text-center py-16"
        >
          <Clock size={40} className="mx-auto text-editorial-gray-light mb-4" />
          <p className="text-editorial-gray text-sm">
            Tu historial de pruebas virtuales aparecerá aquí.
          </p>
          <button
            onClick={() => navigate("/virtual-try-on")}
            className="btn-primary mt-6 inline-flex items-center gap-2"
          >
            <Camera size={14} />
            Probar con IA
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}

export default Profile;
