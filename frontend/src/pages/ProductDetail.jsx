import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Sparkles, Heart, ExternalLink } from "lucide-react";
import { fetchProductById } from "../store/productSlice";
import { toggleFavorite, fetchFavorites } from "../store/favoritesSlice";
import { openVtonModal } from "../store/uiSlice";

function ProductDetail() {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { selectedProduct, loading } = useSelector((state) => state.products);
  const { favorites } = useSelector((state) => state.favorites);
  const { isAuthenticated } = useSelector((state) => state.user);
  const [selectedSize, setSelectedSize] = useState("");
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedImage, setSelectedImage] = useState(0);

  const isFav = favorites.includes(id);

  useEffect(() => {
    dispatch(fetchProductById(id));
    if (isAuthenticated) {
      dispatch(fetchFavorites());
    }
    window.scrollTo(0, 0);
  }, [dispatch, id, isAuthenticated]);

  useEffect(() => {
    if (selectedProduct) {
      setSelectedSize(selectedProduct.sizes?.[0] || "");
      setSelectedColor(selectedProduct.colors?.[0] || "");
    }
  }, [selectedProduct]);

  const handleTryOn = () => {
    if (selectedProduct) {
      dispatch(openVtonModal(selectedProduct));
    }
  };

  const handleToggleFavorite = () => {
    if (isAuthenticated) {
      dispatch(toggleFavorite(id));
    }
  };

  if (loading || !selectedProduct) {
    return (
      <div className="flex justify-center items-center py-32">
        <div className="w-8 h-8 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
      </div>
    );
  }

  const images = selectedProduct.image_urls?.length
    ? selectedProduct.image_urls
    : [selectedProduct.image_url];

  return (
    <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-8">
      {/* Back Link */}
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        className="mb-8"
      >
        <Link
          to="/catalog"
          className="inline-flex items-center gap-2 text-xs text-editorial-gray hover:text-editorial-black transition-colors tracking-wide"
        >
          <ArrowLeft size={14} />
          Volver al catalogo
        </Link>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-16">
        {/* Images */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="aspect-[3/4] rounded-2xl overflow-hidden bg-editorial-cream-dark mb-4">
            <AnimatePresence mode="wait">
              <motion.img
                key={selectedImage}
                src={images[selectedImage]}
                alt={selectedProduct.name}
                className="w-full h-full object-cover"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              />
            </AnimatePresence>
          </div>

          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`w-16 h-20 rounded-lg overflow-hidden border flex-shrink-0 transition-all duration-200 ${
                    selectedImage === idx
                      ? "border-editorial-black"
                      : "border-transparent opacity-60 hover:opacity-100"
                  }`}
                >
                  <img src={img} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </motion.div>

        {/* Product Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="md:py-4"
        >
          <div className="mb-6">
            <span className="editorial-label text-[10px] bg-editorial-cream-dark text-editorial-gray px-3 py-1 rounded-full inline-block">
              {selectedProduct.store}
            </span>
          </div>

          <h1 className="text-2xl md:text-3xl font-display font-semibold text-editorial-black mb-3 leading-tight">
            {selectedProduct.name}
          </h1>

          <p className="text-xl font-semibold text-editorial-black tabular-nums mb-6">
            {selectedProduct.currency === "CLP" ? "$" : selectedProduct.currency || "$"}
            {selectedProduct.price?.toLocaleString("es-CL")}
          </p>

          {selectedProduct.description && (
            <p className="text-sm text-editorial-gray leading-relaxed mb-8">
              {selectedProduct.description}
            </p>
          )}

          {/* Sizes */}
          {selectedProduct.sizes && selectedProduct.sizes.length > 0 && (
            <div className="mb-6">
              <h3 className="editorial-label mb-3">Talla</h3>
              <div className="flex flex-wrap gap-2">
                {selectedProduct.sizes.map((size) => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`min-w-[44px] h-11 px-4 border rounded-lg text-xs font-medium transition-all duration-200 ${
                      selectedSize === size
                        ? "border-editorial-black bg-editorial-black text-white"
                        : "border-editorial-black/10 text-editorial-black hover:border-editorial-black/30"
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Colors */}
          {selectedProduct.colors && selectedProduct.colors.length > 0 && (
            <div className="mb-8">
              <h3 className="editorial-label mb-3">Color</h3>
              <div className="flex flex-wrap gap-2">
                {selectedProduct.colors.map((color) => (
                  <button
                    key={color}
                    onClick={() => setSelectedColor(color)}
                    className={`px-4 py-2 border rounded-lg text-xs font-medium transition-all duration-200 ${
                      selectedColor === color
                        ? "border-editorial-black bg-editorial-black text-white"
                        : "border-editorial-black/10 text-editorial-black hover:border-editorial-black/30"
                    }`}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* CTAs */}
          <div className="space-y-3">
            <button onClick={handleTryOn} className="btn-primary w-full flex items-center justify-center gap-2">
              <Sparkles size={16} />
              Probar con IA Try-On
            </button>
            <div className="flex gap-3">
              {isAuthenticated && (
                <button
                  onClick={handleToggleFavorite}
                  className={`btn-outline flex-1 flex items-center justify-center gap-2 ${
                    isFav ? "border-red-500 text-red-500" : ""
                  }`}
                >
                  <Heart size={16} className={isFav ? "fill-red-500" : ""} />
                  {isFav ? "En Favoritos" : "Favoritos"}
                </button>
              )}
              {selectedProduct.original_url && (
                <a
                  href={selectedProduct.original_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-outline flex-1 flex items-center justify-center gap-2"
                >
                  <ExternalLink size={16} />
                  Ver prenda
                </a>
              )}
            </div>
          </div>

          {/* Product Details */}
          <div className="mt-10 pt-8 border-t border-editorial-black/5">
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="editorial-label">Tienda</span>
                <p className="text-editorial-black mt-1">{selectedProduct.store}</p>
              </div>
              <div>
                <span className="editorial-label">Categoria</span>
                <p className="text-editorial-black mt-1">{selectedProduct.category || "N/A"}</p>
              </div>
              <div>
                <span className="editorial-label">Disponibilidad</span>
                <p className="text-editorial-black mt-1">
                  {selectedProduct.availability !== false ? "Disponible" : "Agotado"}
                </p>
              </div>
              <div>
                <span className="editorial-label">Moneda</span>
                <p className="text-editorial-black mt-1">{selectedProduct.currency || "CLP"}</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default ProductDetail;
