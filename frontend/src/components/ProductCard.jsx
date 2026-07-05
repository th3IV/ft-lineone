import { Link } from "react-router-dom";
import { Heart } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";
import { toggleFavorite } from "../store/favoritesSlice";

function ProductCard({ product, onTryOn, index = 0 }) {
  const dispatch = useDispatch();
  const { favorites } = useSelector((state) => state.favorites);
  const { isAuthenticated } = useSelector((state) => state.user);
  const isFav = favorites.includes(product.id);

  return (
    <div
      className="group editorial-card card-shadow animate-fade-in"
      style={{ animationDelay: `${(index % 20) * 60}ms`, animationFillMode: "both" }}
    >
      <div className="relative aspect-[3/4] overflow-hidden bg-editorial-cream-dark">
        <Link to={`/product/${product.id}`}>
          <img
            src={product.image_url || "/placeholder.jpg"}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-[1.04] transition-transform duration-700 ease-out"
          />
        </Link>

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-editorial-black/0 group-hover:bg-editorial-black/10 transition-colors duration-500" />

        {/* Store Badge */}
        <div className="absolute top-3 left-3">
          <span className="editorial-label text-[9px] bg-editorial-white/90 backdrop-blur-sm text-editorial-black px-2.5 py-1 rounded-full">
            {product.store}
          </span>
        </div>

        {/* Heart Button */}
        {isAuthenticated && (
          <button
            className="absolute top-3 right-3 w-8 h-8 rounded-full bg-editorial-white/80 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 hover:bg-editorial-white"
            onClick={(e) => {
              e.preventDefault();
              dispatch(toggleFavorite(product.id));
            }}
          >
            <Heart
              size={14}
              className={`transition-colors ${
                isFav ? "text-red-500 fill-red-500" : "text-editorial-gray hover:text-red-500"
              }`}
            />
          </button>
        )}

        {/* Try-On Button */}
        <button
          onClick={() => onTryOn && onTryOn(product)}
          className="absolute bottom-3 left-3 right-3 py-2.5 bg-editorial-white/90 backdrop-blur-sm text-editorial-black text-xs font-medium tracking-wide rounded-xl opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 hover:bg-editorial-white"
        >
          Probar con IA
        </button>
      </div>

      <div className="p-4">
        <Link to={`/product/${product.id}`}>
           <h3 className="text-[13px] font-medium text-editorial-black truncate transition-colors duration-200">
            {product.name}
          </h3>
        </Link>
        <p className="text-sm font-semibold text-editorial-black mt-1 tabular-nums">
          {product.currency === "CLP" ? "$" : product.currency || "$"}
          {Number(product.price)?.toLocaleString("es-CL")}
        </p>
      </div>
    </div>
  );
}

export default ProductCard;
