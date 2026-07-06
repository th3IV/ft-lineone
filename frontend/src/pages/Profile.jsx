import { useState, useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { User, Settings, Clock, Sparkles, Heart, Camera, Shirt } from "lucide-react";
import toast from "react-hot-toast";
import { fetchProfile, updateProfile, updateMeasurements, updatePreferences, uploadProfileImage } from "../store/userSlice";
import { fetchFavorites } from "../store/favoritesSlice";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ProductGrid from "../components/ProductGrid";
import VtonHistory from "../components/VtonHistory";

const MEASUREMENTS_DEFAULT = {
  height: "",
  weight: "",
  chest: "",
  waist: "",
  hips: "",
  bodyShape: "",
};

const PREFERENCES_DEFAULT = {
  sizes: { upper: "", lower: "" },
  brands: [],
  colors: [],
  styles: [],
};

const QUIZ_COLORS = ["negro", "blanco", "gris", "azul", "beige", "marrón", "verde", "rosa"];
const QUIZ_STYLES = ["minimalista", "streetwear", "casual", "formal", "bohemio", "deportivo"];
const QUIZ_OCCASIONS = ["oficina", "cafe", "fiesta", "gym", "paseo", "formal"];
const BODY_SHAPES = ["reloj", "pera", "rectangulo", "triangulo", "ovalo"];

function Profile() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, loading } = useSelector((state) => state.user);
  const { products: favoriteProducts, loading: favLoading } = useSelector((state) => state.favorites);

  const [profile, setProfile] = useState(user || {});
  const [measurements, setMeasurements] = useState(MEASUREMENTS_DEFAULT);
  const [preferences, setPreferences] = useState(PREFERENCES_DEFAULT);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState("profile");
  const [imageLoading, setImageLoading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    dispatch(fetchProfile());
    dispatch(fetchFavorites());
  }, [dispatch]);

  useEffect(() => {
    if (user) {
      setProfile(user);
      if (user.body_measurements) setMeasurements(user.body_measurements);
      if (user.preferences) setPreferences(user.preferences);
    }
  }, [user]);

  const handleSave = async () => {
    await dispatch(updateProfile({ name: profile.name, gender: profile.gender }));
    setIsEditing(false);
  };

  const handleImageClick = () => {
    fileInputRef.current?.click();
  };

  const handleImageChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImageLoading(true);
    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64 = reader.result;
        await dispatch(uploadProfileImage(base64));
        setImageLoading(false);
      };
      reader.readAsDataURL(file);
    } catch {
      setImageLoading(false);
    }
  };

  const tabs = [
    { id: "profile", label: "Perfil", icon: User },
    { id: "measurements", label: "Medidas", icon: Settings },
    { id: "preferences", label: "Preferencias", icon: Sparkles },
    { id: "quiz", label: "Quiz", icon: Shirt },
    { id: "favorites", label: "Favoritos", icon: Heart },
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
          <div className="flex items-center gap-6">
            <div
              onClick={handleImageClick}
              className="relative w-24 h-24 rounded-full overflow-hidden border-2 border-editorial-gray-light cursor-pointer group shrink-0"
            >
              {profile.profile_image ? (
                <img
                  src={profile.profile_image}
                  alt={profile.name || "Usuario"}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-editorial-gray-light/30 text-editorial-gray">
                  <User size={32} />
                </div>
              )}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera size={20} className="text-white" />
              </div>
              {imageLoading && (
                <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                  <div className="w-6 h-6 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
                </div>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="hidden"
            />
            <div>
              <h2 className="text-lg font-display font-semibold text-editorial-black">
                {profile.name || "Usuario"}
              </h2>
              <p className="text-sm text-editorial-gray-light">{profile.email || ""}</p>
              <button
                onClick={handleImageClick}
                className="text-xs text-editorial-gray underline mt-2 hover:text-editorial-black"
              >
                Cambiar foto de perfil
              </button>
            </div>
          </div>

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
              chest: "Busto (cm)",
              waist: "Cintura (cm)",
              hips: "Caderas (cm)",
            })
              .filter(([key]) => {
                if (profile.gender === "masculino") {
                  return !["chest", "waist"].includes(key);
                }
                return true;
              })
              .map(([key, label]) => (
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
              onClick={async () => {
                await dispatch(updateMeasurements(measurements));
                toast.success("Medidas guardadas");
              }}
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
            <div className="grid grid-cols-2 gap-4 mt-2">
              {Object.entries({
                upper: "Parte superior",
                lower: "Parte inferior",
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
            <button onClick={async () => {
              await dispatch(updatePreferences(preferences));
              toast.success("Preferencias guardadas");
            }} className="btn-primary">
              Guardar Preferencias
            </button>
          </div>
        </motion.div>
      )}

      {/* Quiz Tab */}
      {activeTab === "quiz" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-8"
        >
          <div className="bg-editorial-gray-light/10 p-6 rounded-lg border border-editorial-gray-light">
            <h3 className="text-lg font-display font-semibold text-editorial-black mb-2">
              Tu estilo en 1 minuto
            </h3>
            <p className="text-sm text-editorial-gray mb-6">
              Responde este quiz para que nuestro asistente te recomiende prendas que encajen contigo.
            </p>

            <div className="space-y-6">
              <div>
                <label className="editorial-label">¿Qué formas de cuerpo te identifican?</label>
                <div className="flex gap-3 mt-2 flex-wrap">
                  {BODY_SHAPES.map((shape) => (
                    <button
                      key={shape}
                      onClick={() => setMeasurements({ ...measurements, bodyShape: shape })}
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

              <div>
                <label className="editorial-label">¿Qué colores prefieres?</label>
                <div className="flex gap-3 mt-2 flex-wrap">
                  {QUIZ_COLORS.map((color) => (
                    <button
                      key={color}
                      onClick={() => {
                        const colors = preferences.colors || [];
                        const updated = colors.includes(color)
                          ? colors.filter((c) => c !== color)
                          : [...colors, color];
                        setPreferences({ ...preferences, colors: updated });
                      }}
                      className={`px-4 py-2 rounded-full text-xs capitalize transition-all ${
                        preferences.colors?.includes(color)
                          ? "bg-editorial-black text-white"
                          : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                      }`}
                    >
                      {color}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="editorial-label">¿Qué estilos te representan?</label>
                <div className="flex gap-3 mt-2 flex-wrap">
                  {QUIZ_STYLES.map((style) => (
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
                  ))}
                </div>
              </div>

              <div>
                <label className="editorial-label">¿Para qué ocasiones buscas ropa?</label>
                <div className="flex gap-3 mt-2 flex-wrap">
                  {QUIZ_OCCASIONS.map((occasion) => (
                    <button
                      key={occasion}
                      onClick={() => {
                        const occasions = preferences.occasions || [];
                        const updated = occasions.includes(occasion)
                          ? occasions.filter((o) => o !== occasion)
                          : [...occasions, occasion];
                        setPreferences({ ...preferences, occasions: updated });
                      }}
                      className={`px-4 py-2 rounded-full text-xs capitalize transition-all ${
                        preferences.occasions?.includes(occasion)
                          ? "bg-editorial-black text-white"
                          : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                      }`}
                    >
                      {occasion}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {Object.entries({ upper: "Talla superior", lower: "Talla inferior" }).map(([key, label]) => (
                  <div key={key}>
                    <label className="editorial-label">{label}</label>
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

            <div className="flex justify-end gap-3 pt-6">
              <button
                onClick={async () => {
                  await dispatch(updateMeasurements(measurements));
                  await dispatch(updatePreferences(preferences));
                  toast.success("Perfil de estilo guardado");
                }}
                className="btn-primary"
              >
                Guardar mi perfil de estilo
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Favorites Tab */}
      {activeTab === "favorites" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {favLoading ? (
            <div className="flex justify-center py-16">
              <div className="w-8 h-8 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
            </div>
          ) : favoriteProducts.length > 0 ? (
            <ProductGrid products={favoriteProducts} loading={false} />
          ) : (
            <div className="text-center py-16">
              <Heart size={40} className="mx-auto text-editorial-gray-light mb-4" />
              <p className="text-editorial-gray text-sm">
                Todavia no tienes favoritos. Explora el catalogo y guarda las prendas que te gusten.
              </p>
              <button
                onClick={() => navigate("/catalog")}
                className="btn-primary mt-6"
              >
                Explorar catalogo
              </button>
            </div>
          )}
        </motion.div>
      )}

      {/* History Tab */}
      {activeTab === "history" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <VtonHistory />
        </motion.div>
      )}
    </motion.div>
  );
}

export default Profile;
