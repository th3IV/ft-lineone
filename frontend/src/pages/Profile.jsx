import { useState, useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { User, Settings, Clock, Sparkles, Heart, Camera, Image as ImageIcon, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { fetchProfile, updateProfile, updateMeasurements, updatePreferences, uploadProfileImage, deleteProfileImage, logoutUser } from "../store/userSlice";
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
  occasions: [],
};

const QUIZ_COLORS = ["negro", "blanco", "gris", "azul", "beige", "marrón", "verde", "rosa", "rojo", "naranja", "amarillo", "morado", "turquesa", "dorado"];
const QUIZ_STYLES = ["minimalista", "streetwear", "casual", "formal", "bohemio", "deportivo", "elegante", "urbano", "vintage", "artístico", "clásico", "moderno"];
const QUIZ_OCCASIONS = ["oficina", "café", "fiesta", "gym", "paseo", "formal", "viaje", "cita", "playa", "deporte"];
const BODY_SHAPES = ["reloj", "pera", "rectangulo", "triangulo", "ovalo"];

function Profile() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user, loading, measurements: savedMeasurements, preferences: savedPreferences } = useSelector((state) => state.user);
  const { products: favoriteProducts, loading: favLoading } = useSelector((state) => state.favorites);

  const [profile, setProfile] = useState(user || {});
  const [measurements, setMeasurements] = useState(MEASUREMENTS_DEFAULT);
  const [preferences, setPreferences] = useState(PREFERENCES_DEFAULT);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState("profile");
  const [imageLoading, setImageLoading] = useState(false);
  const [showAvatarMenu, setShowAvatarMenu] = useState(false);
  const [editingSection, setEditingSection] = useState(null);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const avatarMenuRef = useRef(null);
  const tabsRef = useRef(null);

  useEffect(() => {
    dispatch(fetchProfile());
    dispatch(fetchFavorites());
  }, [dispatch]);

  useEffect(() => {
    if (user) {
      setProfile(user);
    }
    if (savedMeasurements && Object.keys(savedMeasurements).length > 0) {
      setMeasurements({ ...MEASUREMENTS_DEFAULT, ...savedMeasurements });
    }
    if (savedPreferences && Object.keys(savedPreferences).length > 0) {
      setPreferences({
        sizes: savedPreferences.sizes || { upper: "", lower: "" },
        brands: savedPreferences.brands || [],
        colors: savedPreferences.colors || [],
        styles: savedPreferences.styles || [],
        occasions: savedPreferences.occasions || [],
      });
    }
  }, [user, savedMeasurements, savedPreferences]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (avatarMenuRef.current && !avatarMenuRef.current.contains(e.target)) {
        setShowAvatarMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSave = async () => {
    await dispatch(updateProfile({ name: profile.name, gender: profile.gender, age: profile.age }));
    setIsEditing(false);
  };

  const handleImageClick = () => {
    setShowAvatarMenu((prev) => !prev);
  };

  const handleSelectGallery = () => {
    setShowAvatarMenu(false);
    fileInputRef.current?.click();
  };

  const handleTakePhoto = () => {
    setShowAvatarMenu(false);
    cameraInputRef.current?.click();
  };

  const handleRemovePhoto = async () => {
    setShowAvatarMenu(false);
    try {
      await dispatch(deleteProfileImage());
      toast.success("Foto eliminada");
    } catch {
      toast.error("Error al eliminar la foto");
    }
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
    { id: "profile", label: "Perfil", shortLabel: "Perfil", icon: User },
    { id: "measurements", label: "Medidas", shortLabel: "Medidas", icon: Settings },
    { id: "preferences", label: "Preferencias", shortLabel: "Prefs", icon: Sparkles },
    { id: "favorites", label: "Favoritos", shortLabel: "Favs", icon: Heart },
    { id: "history", label: "Historial", shortLabel: "Historial", icon: Clock },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="max-w-[1000px] mx-auto px-4 sm:px-8 py-6 sm:py-10"
    >
      <h1 className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-editorial-black mb-6 sm:mb-8">
        Mi Cuenta
      </h1>

      {/* Tabs - Mobile: scrollable horizontal, Desktop: normal */}
      <div
        ref={tabsRef}
        className="flex overflow-x-auto gap-0 border-b border-editorial-gray-light mb-6 sm:mb-8 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0"
        style={{ WebkitOverflowScrolling: "touch", scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2.5 sm:py-3 text-[10px] sm:text-xs uppercase tracking-widest border-b -mb-px transition-colors whitespace-nowrap shrink-0 ${
              activeTab === tab.id
                ? "border-editorial-black text-editorial-black font-medium"
                : "border-transparent text-editorial-gray-light hover:text-editorial-gray"
            }`}
          >
            <tab.icon size={14} />
            <span className="hidden sm:inline">{tab.label}</span>
            <span className="sm:hidden">{tab.shortLabel}</span>
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === "profile" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-5 sm:space-y-8"
        >
          {/* Avatar + Name */}
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 sm:gap-6">
            <div ref={avatarMenuRef} className="relative shrink-0">
              <div
                onClick={handleImageClick}
                className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-full overflow-hidden border-2 border-editorial-gray-light cursor-pointer group"
              >
                {profile.profile_image ? (
                  <img
                    src={profile.profile_image}
                    alt={profile.name || "Usuario"}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-editorial-gray-light/30 text-editorial-gray">
                    <User size={28} className="sm:hidden" />
                    <User size={32} className="hidden sm:block" />
                  </div>
                )}
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <Camera size={18} className="text-white sm:hidden" />
                  <Camera size={20} className="text-white hidden sm:block" />
                </div>
                {imageLoading && (
                  <div className="absolute inset-0 bg-white/70 flex items-center justify-center">
                    <div className="w-6 h-6 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
                  </div>
                )}
              </div>

              {showAvatarMenu && (
                <motion.div
                  initial={{ opacity: 0, y: 4, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 4, scale: 0.96 }}
                  transition={{ duration: 0.15 }}
                  className="absolute top-full left-0 mt-2 w-48 bg-white rounded-xl shadow-[0_12px_40px_rgba(0,0,0,0.12)] border border-editorial-black/5 overflow-hidden z-20"
                >
                  <button
                    onClick={handleSelectGallery}
                    className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-editorial-black hover:bg-editorial-cream transition-colors"
                  >
                    <ImageIcon size={16} className="text-editorial-gray" />
                    Agregar imagen
                  </button>
                  <button
                    onClick={handleTakePhoto}
                    className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-editorial-black hover:bg-editorial-cream transition-colors"
                  >
                    <Camera size={16} className="text-editorial-gray" />
                    Sacar foto
                  </button>
                  {profile.profile_image && (
                    <button
                      onClick={handleRemovePhoto}
                      className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 size={16} />
                      Eliminar foto
                    </button>
                  )}
                </motion.div>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              className="hidden"
            />
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="user"
              onChange={handleImageChange}
              className="hidden"
            />
            <div className="text-center sm:text-left">
              <h2 className="text-lg font-display font-semibold text-editorial-black">
                {profile.name || "Usuario"}
              </h2>
              <p className="text-sm text-editorial-gray-light">{profile.email || ""}</p>
            </div>
          </div>

          {/* Name + Email + Age */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
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
            <div>
              <label className="editorial-label">Edad</label>
              <input
                type="number"
                min="13"
                max="120"
                value={profile.age || ""}
                onChange={(e) => setProfile({ ...profile, age: e.target.value ? parseInt(e.target.value) : "" })}
                disabled={!isEditing}
                className="input-line w-full"
                placeholder="Ej: 28"
              />
            </div>
          </div>

          {/* Gender */}
          <div>
            <label className="editorial-label">Género</label>
            <div className="flex gap-2 sm:gap-3 mt-2 flex-wrap">
              {["femenino", "masculino", "unisex", "otro"].map((g) => (
                <button
                  key={g}
                  onClick={() => isEditing && setProfile({ ...profile, gender: g })}
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-[10px] sm:text-xs transition-all ${
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

          {/* Edit/Save buttons */}
          <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4">
            {isEditing ? (
              <>
                <button
                  onClick={() => setIsEditing(false)}
                  className="btn-outline w-full sm:w-auto"
                >
                  Cancelar
                </button>
                <button onClick={handleSave} className="btn-primary w-full sm:w-auto">
                  Guardar
                </button>
              </>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="btn-primary w-full sm:w-auto"
              >
                Editar Perfil
              </button>
            )}
          </div>

          <div className="pt-4 border-t border-editorial-gray-light">
            <button
              onClick={async () => {
                await dispatch(logoutUser());
                navigate("/");
              }}
              className="w-full py-2.5 px-4 bg-red-500/10 text-red-400 rounded-xl border border-red-500/20 hover:bg-red-500/20 transition-all text-sm font-medium"
            >
              Cerrar sesión
            </button>
          </div>
        </motion.div>
      )}

      {/* Measurements Tab */}
      {activeTab === "measurements" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-5 sm:space-y-8"
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-6">
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
                <label className="editorial-label text-[10px] sm:text-xs">{label}</label>
                <input
                  type="number"
                  value={measurements[key] || ""}
                  onChange={(e) =>
                    setMeasurements({ ...measurements, [key]: e.target.value })
                  }
                  disabled={editingSection !== "measurements"}
                  className={`input-line w-full text-sm ${editingSection !== "measurements" ? "opacity-60 cursor-not-allowed" : ""}`}
                />
              </div>
            ))}
          </div>

          <div>
            <label className="editorial-label">Forma del cuerpo</label>
            <div className="flex gap-2 sm:gap-3 mt-2 flex-wrap">
              {["reloj", "pera", "rectangulo", "triangulo", "ovalo"].map((shape) => (
                <button
                  key={shape}
                  onClick={() =>
                    editingSection === "measurements" && setMeasurements({ ...measurements, bodyShape: shape })
                  }
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-[10px] sm:text-xs capitalize transition-all ${
                    measurements.bodyShape === shape
                      ? "bg-editorial-black text-white"
                      : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                  } ${editingSection !== "measurements" ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  {shape}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4">
            {editingSection === "measurements" ? (
              <>
                <button
                  onClick={() => setEditingSection(null)}
                  className="btn-outline w-full sm:w-auto"
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    await dispatch(updateMeasurements(measurements));
                    toast.success("Medidas guardadas");
                    setEditingSection(null);
                  }}
                  className="btn-primary w-full sm:w-auto"
                >
                  Guardar
                </button>
              </>
            ) : (
              <button
                onClick={() => setEditingSection("measurements")}
                className="btn-primary w-full sm:w-auto"
              >
                Editar
              </button>
            )}
          </div>
        </motion.div>
      )}

      {/* Preferences Tab */}
      {activeTab === "preferences" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-5 sm:space-y-8"
        >
          <div>
            <label className="editorial-label">¿Qué formas de cuerpo te identifican?</label>
            <div className="flex gap-2 sm:gap-3 mt-2 flex-wrap">
              {BODY_SHAPES.map((shape) => (
                <button
                  key={shape}
                  onClick={() => {
                    if (editingSection !== "preferences") return;
                    setMeasurements({ ...measurements, bodyShape: shape });
                  }}
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-[10px] sm:text-xs capitalize transition-all ${
                    measurements.bodyShape === shape
                      ? "bg-editorial-black text-white"
                      : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                  } ${editingSection !== "preferences" ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  {shape}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="editorial-label">Estilos que te gustan</label>
            <div className="flex gap-2 sm:gap-3 mt-2 flex-wrap">
              {QUIZ_STYLES.map((style) => (
                <button
                  key={style}
                  onClick={() => {
                    if (editingSection !== "preferences") return;
                    const styles = preferences.styles || [];
                    const updated = styles.includes(style)
                      ? styles.filter((s) => s !== style)
                      : [...styles, style];
                    setPreferences({ ...preferences, styles: updated });
                  }}
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-[10px] sm:text-xs capitalize transition-all ${
                    preferences.styles?.includes(style)
                      ? "bg-editorial-black text-white"
                      : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                  } ${editingSection !== "preferences" ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  {style}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="editorial-label">Colores preferidos</label>
            <div className="flex gap-2 sm:gap-3 mt-2 flex-wrap">
              {QUIZ_COLORS.map((color) => (
                <button
                  key={color}
                  onClick={() => {
                    if (editingSection !== "preferences") return;
                    const colors = preferences.colors || [];
                    const updated = colors.includes(color)
                      ? colors.filter((c) => c !== color)
                      : [...colors, color];
                    setPreferences({ ...preferences, colors: updated });
                  }}
                  className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full border-2 transition-all ${
                    preferences.colors?.includes(color)
                      ? "border-editorial-black scale-110"
                      : "border-editorial-gray-light hover:border-editorial-gray"
                  } ${editingSection !== "preferences" ? "opacity-50 cursor-not-allowed" : ""}`}
                  style={{
                    backgroundColor:
                      color === "negro" ? "#000"
                      : color === "blanco" ? "#fff"
                      : color === "gris" ? "#9CA3AF"
                      : color === "azul" ? "#3B82F6"
                      : color === "beige" ? "#D4C5A9"
                      : color === "marrón" ? "#92400E"
                      : color === "verde" ? "#22C55E"
                      : color === "rosa" ? "#F472B6"
                      : color === "rojo" ? "#EF4444"
                      : color === "naranja" ? "#F97316"
                      : color === "amarillo" ? "#EAB308"
                      : color === "morado" ? "#A855F7"
                      : color === "turquesa" ? "#14B8A6"
                      : "#D4AF37",
                  }}
                />
              ))}
            </div>
          </div>

          <div>
            <label className="editorial-label">¿Para qué ocasiones buscas ropa?</label>
            <div className="flex gap-2 sm:gap-3 mt-2 flex-wrap">
              {QUIZ_OCCASIONS.map((occasion) => (
                <button
                  key={occasion}
                  onClick={() => {
                    if (editingSection !== "preferences") return;
                    const occasions = preferences.occasions || [];
                    const updated = occasions.includes(occasion)
                      ? occasions.filter((o) => o !== occasion)
                      : [...occasions, occasion];
                    setPreferences({ ...preferences, occasions: updated });
                  }}
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-[10px] sm:text-xs capitalize transition-all ${
                    preferences.occasions?.includes(occasion)
                      ? "bg-editorial-black text-white"
                      : "border border-editorial-gray-light text-editorial-gray hover:border-editorial-black"
                  } ${editingSection !== "preferences" ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  {occasion}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4">
            {editingSection === "preferences" ? (
              <>
                <button
                  onClick={() => setEditingSection(null)}
                  className="btn-outline w-full sm:w-auto"
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    await dispatch(updateMeasurements(measurements));
                    await dispatch(updatePreferences(preferences));
                    toast.success("Preferencias guardadas");
                    setEditingSection(null);
                  }}
                  className="btn-primary w-full sm:w-auto"
                >
                  Guardar
                </button>
              </>
            ) : (
              <button
                onClick={() => setEditingSection("preferences")}
                className="btn-primary w-full sm:w-auto"
              >
                Editar
              </button>
            )}
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
            <div className="text-center py-12 sm:py-16">
              <Heart size={36} className="mx-auto text-editorial-gray-light mb-4" />
              <p className="text-editorial-gray text-xs sm:text-sm">
                Todavia no tienes favoritos. Explora el catalogo y guarda las prendas que te gusten.
              </p>
              <button
                onClick={() => navigate("/catalog")}
                className="btn-primary mt-4 sm:mt-6 w-full sm:w-auto"
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
