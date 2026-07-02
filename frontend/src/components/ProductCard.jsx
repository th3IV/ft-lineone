import { Link } from "react-router-dom";

const storeColors = {
  paris: "bg-blue-600",
  maui: "bg-teal-500",
  zara: "bg-black",
};

function ProductCard({ product, onTryOn, index = 0 }) {
  const storeKey = product.store?.toLowerCase();
  const storeColor = storeColors[storeKey] || "bg-gray-600";

  return (
    <div
      className="group bg-white rounded-2xl card-shadow overflow-hidden transition-all duration-500 hover:-translate-y-1 animate-fade-in"
      style={{ animationDelay: `${(index % 20) * 50}ms`, animationFillMode: "both" }}
    >
      <div className="relative aspect-square overflow-hidden bg-gray-100">
        <Link to={`/product/${product.id}`}>
          <img
            src={product.image_url || "/placeholder.jpg"}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
          />
        </Link>
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        <div className="absolute top-3 left-3 flex gap-1.5">
          <span className={`${storeColor} text-white text-[10px] font-semibold px-2.5 py-1 rounded-full shadow-lg`}>
            {product.store}
          </span>
        </div>
        <button
          onClick={() => onTryOn && onTryOn(product)}
          className="absolute bottom-3 left-3 right-3 btn-primary text-sm text-center opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 shadow-lg"
        >
          Probar ahora
        </button>
      </div>
      <div className="p-4">
        <Link to={`/product/${product.id}`}>
          <h3 className="text-sm font-medium text-gray-900 truncate group-hover:text-fashion-pink transition-colors">
            {product.name}
          </h3>
        </Link>
        <p className="text-lg font-bold bg-gradient-to-r from-fashion-pink to-fashion-purple bg-clip-text text-transparent mt-1">
          {product.currency || "$"}{Number(product.price)?.toLocaleString("es-CL")}
        </p>
      </div>
    </div>
  );
}

export default ProductCard;
