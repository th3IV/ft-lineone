import { useState, useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { User, Settings, Clock, Sparkles, Heart, Camera, Image as ImageIcon, Trash2, Crown, Zap, LogOut } from "lucide-react";
import toast from "react-hot-toast";
import { fetchProfile, updateProfile, updateMeasurements, updatePreferences, uploadProfileImage, deleteProfileImage, logoutUser } from "../store/userSlice";
import { fetchFavorites } from "../store/favoritesSlice";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ProductGrid from "../components/ProductGrid";
import VtonHistory from "../components/VtonHistory";
import { useFeatureGate } from "../hooks/useFeatureGate";
import UpgradeModal from "../components/UpgradeModal";
import RemainingUses from "../components/RemainingUses";
import PremiumBadge from "../components/PremiumBadge";
import ImageCropModal from "../components/ImageCropModal";

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
  const { user, loading, measurements: savedMeasurements, preferences: savedPreferences, dailyUsage } = useSelector((state) => state.user);
  const { products: favoriteProducts, loading: favLoading } = useSelector((state) => state.favorites);
  const {
    isPremium,
    vtonUsed,
    llmUsed,
    getUsageColor,
    showUpgrade,
    showUpgradeModal,
    hideUpgradeModal,
    handleUpgrade,
    upgradeLoading,
    upgradeError,
    limits,
  } = useFeatureGate();

  const [profile, setProfile] = useState(user || {});
  const [measurements, setMeasurements] = useState(MEASUREMENTS_DEFAULT);
  const [preferences, setPreferences] = useState(PREFERENCES_DEFAULT);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState("profile");
  const [imageLoading, setImageLoading] = useState(false);
  const [cropModalImage, setCropModalImage] = useState(null);
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
      const m = user.body_measurements || {};
      setMeasurements({ ...MEASUREMENTS_DEFAULT, ...m });
      const p = user.preferences || {};
      setPreferences({
        sizes: p.sizes || { upper: "", lower: "" },
        brands: p.brands || [],
        colors: p.colors || [],
        styles: p.styles || [],
        occasions: p.occasions || [],
      });
    }
  }, [user]);

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
    const result = await dispatch(deleteProfileImage());
    if (result.meta.requestStatus === "fulfilled") {
      setProfile((prev) => ({ ...prev, profile_image: null }));
      toast.success("Foto eliminada");
    } else {
      toast.error("Error al eliminar foto");
    }
  };

  const handleImageChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImageLoading(true);
    const reader = new FileReader();
    reader.onloadend = () => {
      setCropModalImage(reader.result);
      setImageLoading(false);
    };
    reader.readAsDataURL(file);
  };

  const handleCropConfirm = async (croppedBase64) => {
    setCropModalImage(null);
    setImageLoading(true);
    const result = await dispatch(uploadProfileImage(croppedBase64));
    if (result.meta.requestStatus === "fulfilled") {
      const url = result.payload?.profile_image;
      if (url) setProfile((prev) => ({ ...prev, profile_image: url }));
      toast.success("Foto actualizada");
    } else {
      toast.error("Error al subir foto");
    }
    setImageLoading(false);
  };

  const tabs = [
    { id: "profile", label: "Perfil", shortLabel: "Perfil", icon: User },
    { id: "measurements", label: "Medidas", shortLabel: "Medidas", icon: Settings },
    { id: "preferences", label: "Preferencias", shortLabel: "Prefs", icon: Sparkles },
    { id: "favorites", label: "Favoritos", shortLabel: "Favs", icon: Heart },
    { id: "history", label: "Historial", shortLabel: "Historial", icon: Clock },
  ];

  return (
    <>
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
                {(profile.profile_image || user?.profile_image) ? (
                  <img
                    src={profile.profile_image || user?.profile_image}
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
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-display font-semibold text-editorial-black">
                  {profile.name || "Usuario"}
                </h2>
                {isPremium && <PremiumBadge size="sm" />}
              </div>
              <p className="text-sm text-editorial-gray-light">{profile.email || ""}</p>
            </div>
          </div>

          {/* Usage Stats (Free users only) */}
          {!isPremium && dailyUsage && (
            <div className="bg-editorial-cream/50 rounded-xl p-4 border border-editorial-gray-light">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-medium text-editorial-gray uppercase tracking-wider">Uso diario</h3>
                <span className="text-[10px] text-editorial-gray-light">Plan Gratuito</span>
              </div>
              <div className="space-y-4">
                <RemainingUses
                  type="vton"
                  used={vtonUsed}
                  limit={limits.vton}
                  color={getUsageColor(vtonUsed)}
                />
                <RemainingUses
                  type="llm"
                  used={llmUsed}
                  limit={limits.llm}
                  color={getUsageColor(llmUsed)}
                />
              </div>
              <motion.button
                onClick={showUpgradeModal}
                whileHover={{ scale: 1.03, boxShadow: "0 0 28px rgba(236,72,153,0.35)" }}
                whileTap={{ scale: 0.97 }}
                transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
                className="mt-4 w-full relative overflow-hidden rounded-xl text-sm font-medium text-white cursor-pointer group"
                style={{
                  background: "linear-gradient(135deg, #0a0a0a 0%, #831843 35%, #7c3aed 65%, #0a0a0a 100%)",
                  backgroundSize: "300% 300%",
                  animation: "shimmer 4s ease-in-out infinite",
                }}
              >
                {/* Shimmer overlay */}
                <div
                  className="absolute inset-0 pointer-events-none transition-all duration-500"
                  style={{
                    background: "linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%)",
                    backgroundSize: "200% 200%",
                    animation: "shimmer 3s ease-in-out infinite",
                  }}
                />
                {/* Border glow on hover */}
                <div className="absolute inset-0 rounded-xl border border-white/0 group-hover:border-white/20 transition-all duration-500 pointer-events-none" />
                {/* Extra brillo hover */}
                <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-all duration-500 pointer-events-none" />
                <div className="relative flex items-center justify-center gap-2 py-2.5 px-4">
                  <div className="relative w-6 h-6 rounded-full bg-white/10 flex items-center justify-center shrink-0 animate-pulse-glow group-hover:bg-white/20 transition-all duration-500">
                    <Zap size={12} className="text-editorial-gold relative z-10 transition-all duration-500 group-hover:scale-125 group-hover:rotate-12" />
                  </div>
                  Upgrade a Premium — $4.990/mes
                  <Sparkles size={10} className="text-white/40 animate-sparkle-twinkle group-hover:text-white/80 group-hover:scale-125 transition-all duration-300" />
                </div>
                {/* Sparkles flotantes */}
                <Sparkles size={8} className="absolute top-0.5 right-3 text-white/20 animate-float-particle group-hover:text-white/50 transition-colors duration-500" style={{ animationDelay: "0s" }} />
                <Sparkles size={6} className="absolute bottom-0.5 left-4 text-white/15 animate-float-particle group-hover:text-white/40 transition-colors duration-500" style={{ animationDelay: "1.5s" }} />
              </motion.button>
            </div>
          )}

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
              {["hombre", "mujer", "unisex", "otro"].map((g) => (
                <button
                  key={g}
                  onClick={() => isEditing && setProfile({ ...profile, gender: g })}
                  className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-[10px] sm:text-xs capitalize transition-all ${
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

          <div className="pt-6">
            <button
              onClick={async () => {
                await dispatch(logoutUser());
                navigate("/");
              }}
              className="w-full flex items-center justify-center gap-2.5 py-3 px-4 border border-editorial-gray-light/60 text-editorial-gray rounded-full text-sm font-medium tracking-wide hover:bg-editorial-cream hover:text-editorial-black hover:border-editorial-gray transition-all duration-300 active:scale-[0.97]"
            >
              <LogOut size={15} strokeWidth={1.5} />
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
                if (profile.gender === "hombre") {
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
    <UpgradeModal
      isOpen={showUpgrade}
      onClose={hideUpgradeModal}
      onUpgrade={handleUpgrade}
      loading={upgradeLoading}
      error={upgradeError}
    />
    {cropModalImage && (
      <ImageCropModal
        image={cropModalImage}
        onConfirm={handleCropConfirm}
        onCancel={() => setCropModalImage(null)}
      />
    )}
    </>
  );
}

export default Profile;
