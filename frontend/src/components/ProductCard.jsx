import { Link } from "react-router-dom";

function ProductCard({ product, onTryOn }) {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden transition-transform hover:scale-105">
      <Link to={`/product/${product.id}`}>
        <div className="aspect-square overflow-hidden bg-gray-100">
          <img
            src={product.image_url || "/placeholder.jpg"}
            alt={product.name}
            className="w-full h-full object-cover"
          />
        </div>
      </Link>
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
            {product.store}
          </span>
        </div>
        <Link to={`/product/${product.id}`}>
          <h3 className="text-sm font-medium text-gray-900 truncate">{product.name}</h3>
        </Link>
        <p className="text-lg font-bold text-gray-900 mt-1">
          {product.currency || "$"}{product.price?.toFixed(2)}
        </p>
        <button
          onClick={() => onTryOn && onTryOn(product)}
          className="w-full mt-3 bg-indigo-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          Try On
        </button>
      </div>
    </div>
  );
}

export default ProductCard;
