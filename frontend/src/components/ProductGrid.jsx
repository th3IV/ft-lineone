import ProductCard from "./ProductCard";

function ProductGrid({ products, loading, emptyMessage, onTryOn }) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-2 border-fashion-pink/20 border-t-fashion-pink animate-spin" />
        </div>
      </div>
    );
  }

  if (!products || products.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-gray-400 text-lg font-serif italic">
          {emptyMessage || "No se encontraron productos."}
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
      {products.map((product, i) => (
        <ProductCard key={product.id} product={product} index={i} onTryOn={onTryOn} />
      ))}
    </div>
  );
}

export default ProductGrid;
