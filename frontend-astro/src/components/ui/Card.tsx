import { motion, HTMLMotionProps } from "framer-motion";
import { ForwardRefExoticComponent, RefAttributes } from "react";

interface CardProps extends HTMLMotionProps<"div"> {
  hover?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

export const Card = motion.div as ForwardRefExoticComponent<
  CardProps & RefAttributes<HTMLDivElement>
>;

// Convenience component with hover effect
interface ProductCardProps {
  product: {
    id: string;
    name: string;
    store: string;
    price: number;
    currency: string;
    image_url?: string;
    image_urls?: string[];
    category: string;
    original_url: string;
    sizes: string[];
    colors: string[];
  };
  onClick?: () => void;
  onFavorite?: () => void;
  isFavorite?: boolean;
  onTryOn?: () => void;
}

export const ProductCard = ({ product, onClick, onFavorite, isFavorite, onTryOn }: ProductCardProps) => {
  const imageUrl = product.image_urls?.[0] || product.image_url || "/placeholder-product.jpg";

  return (
    <Card
      className="group relative bg-editorial-white border border-editorial-cream-dark overflow-hidden"
      hover
      whileHover={{ y: -8, boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.15)" }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      onClick={onClick}
      style={{ cursor: onClick ? "pointer" : "default" }}
    >
      <div className="relative aspect-[3/4] overflow-hidden bg-editorial-cream">
        <img
          src={imageUrl}
          alt={product.name}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        
        {/* Favorite button */}
        <button
          onClick={(e) => { e.stopPropagation(); onFavorite?.(); }}
          className={`absolute top-3 right-3 z-10 w-10 h-10 rounded-full bg-editorial-white/90 backdrop-blur-sm flex items-center justify-center 
            transition-all duration-200 
            ${isFavorite ? "text-editorial-terracotta" : "text-editorial-gray hover:text-editorial-terracotta"}
          `}
          aria-label={isFavorite ? "Quitar de favoritos" : "Añadir a favoritos"}
        >
          <svg className="w-5 h-5" fill={isFavorite ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </button>

        {/* Try On button */}
        <motion.button
          onClick={(e) => { e.stopPropagation(); onTryOn?.(); }}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 px-6 py-2.5 bg-editorial-black text-editorial-white font-display text-xs font-medium uppercase tracking-wide rounded-none opacity-0 translate-y-4 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 hover:bg-editorial-gold hover:text-editorial-black"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          Probarme
        </motion.button>
      </div>

      <div className="p-4">
        <p className="text-xs font-medium text-editorial-gold uppercase tracking-wider mb-1">
          {product.store}
        </p>
        <h3 className="font-display text-lg font-medium text-editorial-black line-clamp-2 mb-2">
          {product.name}
        </h3>
        <div className="flex items-center gap-2 mb-3">
          <span className="font-display text-xl font-semibold text-editorial-black">
            {product.price.toLocaleString()} {product.currency}
          </span>
          <span className="text-xs text-editorial-gray-light uppercase tracking-wider">
            {product.category}
          </span>
        </div>
        <div className="flex flex-wrap gap-1">
          {product.sizes.slice(0, 4).map((size) => (
            <span key={size} className="px-2 py-0.5 text-xs bg-editorial-cream-dark text-editorial-gray rounded">
              {size}
            </span>
          ))}
          {product.sizes.length > 4 && (
            <span className="px-2 py-0.5 text-xs bg-editorial-cream-dark text-editorial-gray rounded">
              +{product.sizes.length - 4}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
};

ProductCard.displayName = "ProductCard";