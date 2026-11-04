import { motion } from "framer-motion";
import ProductCard from "./ProductCard";

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

function ProductGrid({ products, loading, emptyMessage, onTryOn }) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="w-8 h-8 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
      </div>
    );
  }

  if (!products || products.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-editorial-gray text-sm font-display italic">
          {emptyMessage || "No se encontraron productos."}
        </p>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-50px" }}
      className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6"
    >
      {products.map((product, i) => (
        <motion.div key={product.id} variants={itemVariants}>
          <ProductCard product={product} index={i} onTryOn={onTryOn} />
        </motion.div>
      ))}
    </motion.div>
  );
}

export default ProductGrid;
