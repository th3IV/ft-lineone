import { useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { ArrowRight, Sparkles, ChevronDown, Store, Shirt } from "lucide-react";
import { fetchProducts } from "../store/productSlice";
import { openVtonModal } from "../store/uiSlice";
import ProductGrid from "../components/ProductGrid";
import RevealOnScroll, {
  StaggerContainer,
  StaggerItem,
} from "../components/RevealOnScroll";

const stores = [
  {
    name: "Paris",
    slug: "paris",
    description: "Elegancia chilena",
    image:
      "https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=600&q=80",
  },
  {
    name: "Maui",
    slug: "maui",
    description: "Estilo playero premium",
    image:
      "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=600&q=80",
  },
  {
    name: "Zara",
    slug: "zara",
    description: "Tendencia global",
    image:
      "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80",
  },
];

function Home() {
  const dispatch = useDispatch();
  const { products, loading } = useSelector((state) => state.products);
  const heroRef = useRef(null);

  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });

  const heroY = useTransform(scrollYProgress, [0, 1], [0, 150]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 1], [1, 1.1]);

  useEffect(() => {
    dispatch(fetchProducts({ limit: 8 }));
  }, [dispatch]);

  const handleTryOn = (product) => {
    dispatch(openVtonModal(product));
  };

  return (
    <div>
      {/* HERO SECTION */}
      <section
        ref={heroRef}
        className="relative h-screen min-h-[600px] max-h-[900px] overflow-hidden"
      >
        {/* Background Image */}
        <motion.div
          style={{ y: heroY, scale: heroScale }}
          className="absolute inset-0"
        >
          <img
            src="/hero.jpg"
            alt="Fashion Editorial"
            className="w-full h-full object-cover"
          />
        </motion.div>

        {/* Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-editorial-black/40 via-editorial-black/20 to-editorial-black/60" />

        {/* Content */}
        <motion.div
          style={{ opacity: heroOpacity }}
          className="relative h-full flex flex-col items-center justify-center text-center px-4"
        >
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="max-w-4xl"
          >
            <p className="editorial-label text-white/60 mb-6 tracking-[0.3em]">
              Virtual Fashion Experience
            </p>
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-display font-semibold text-white leading-[0.9] tracking-tight mb-6">
              Tu estilo,
              <br />
              <span className="italic font-normal text-white/80">
                definido por IA
              </span>
            </h1>
            <p className="text-lg md:text-xl text-white/60 font-light max-w-xl mx-auto mb-10 leading-relaxed">
              Prueba cualquier prenda antes de comprarla. Inteligencia artificial
              que entiende tu cuerpo y tu estilo.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/virtual-try-on"
                className="btn-gradient flex items-center gap-2.5 text-base"
              >
                <Sparkles size={18} />
                Probar ahora
              </Link>
              <Link
                to="/catalog"
                className="btn-outline-white flex items-center gap-2 text-base"
              >
                Explora el catalogo
                <ArrowRight size={16} />
              </Link>
            </div>
          </motion.div>

          {/* Scroll Indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2"
          >
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
              className="flex flex-col items-center gap-2"
            >
              <span className="text-[10px] tracking-[0.3em] uppercase text-white/40">
                Scroll
              </span>
              <ChevronDown size={16} className="text-white/40" />
            </motion.div>
          </motion.div>
        </motion.div>
      </section>

      {/* FEATURED PRODUCTS */}
      <section className="max-w-[1400px] mx-auto px-5 sm:px-8 py-20 md:py-28">
        <RevealOnScroll>
          <div className="flex items-end justify-between mb-12">
            <div>
              <p className="editorial-label mb-3">Destacados</p>
              <h2 className="section-title">
                Lo que esta en tendencia
              </h2>
            </div>
            <Link
              to="/catalog"
              className="hidden sm:flex items-center gap-2 text-sm font-medium text-editorial-gray hover:text-editorial-black transition-colors group"
            >
              Ver todo
              <ArrowRight
                size={14}
                className="group-hover:translate-x-1 transition-transform"
              />
            </Link>
          </div>
        </RevealOnScroll>

        <ProductGrid
          products={products}
          loading={loading}
          onTryOn={handleTryOn}
        />

        <div className="mt-8 text-center sm:hidden">
          <Link
            to="/catalog"
            className="btn-outline inline-flex items-center gap-2"
          >
            Ver todo el catalogo
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>

      {/* AI TRY-ON SHOWCASE */}
      <section className="bg-editorial-cream-dark py-20 md:py-28">
        <div className="max-w-[1400px] mx-auto px-5 sm:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            {/* Image */}
            <RevealOnScroll direction="left">
              <div className="relative aspect-[4/5] rounded-3xl overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&q=80"
                  alt="Virtual Try-On"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-editorial-black/30 to-transparent" />

                {/* Floating Badge */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                  className="absolute bottom-6 left-6 right-6 bg-white/90 backdrop-blur-lg rounded-2xl p-4 flex items-center gap-4"
                >
                   <div className="w-12 h-12 rounded-full bg-editorial-black flex items-center justify-center">
                    <Sparkles size={20} className="text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-editorial-black">
                      IA Try-On
                    </p>
                    <p className="text-xs text-editorial-gray">
                      Resultado en segundos
                    </p>
                  </div>
                </motion.div>
              </div>
            </RevealOnScroll>

            {/* Text */}
            <RevealOnScroll direction="right">
              <div className="lg:pl-8">
                <p className="editorial-label mb-4">Tecnologia de vanguardia</p>
                <h2 className="section-title mb-6">
                  Prueba cualquier prenda
                  <br />
                  <span className="italic font-normal text-editorial-gray">
                    sin salir de casa
                  </span>
                </h2>
                <p className="text-editorial-gray leading-relaxed mb-8 max-w-md">
                  Nuestra IA analiza tu cuerpo y superpone la prenda
                  seleccionada con un realismo impresionante. Sin probadores,
                  sin esperas, sin devoluciones.
                </p>
                <div className="space-y-4 mb-8">
                  {[
                    "Foto instantanea con tu smartphone",
                    "IA que respeta tu contextura",
                    "Resultados en menos de 30 segundos",
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full bg-editorial-black flex items-center justify-center flex-shrink-0">
                        <svg
                          className="w-3 h-3 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={3}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                      <span className="text-sm text-editorial-charcoal">
                        {item}
                      </span>
                    </div>
                  ))}
                </div>
                <Link
                  to="/virtual-try-on"
                  className="btn-primary inline-flex items-center gap-2"
                >
                  <Sparkles size={16} />
                  Probar ahora
                </Link>
              </div>
            </RevealOnScroll>
          </div>
        </div>
      </section>

      {/* STORES */}
      <section className="max-w-[1400px] mx-auto px-5 sm:px-8 py-20 md:py-28">
        <RevealOnScroll>
          <div className="text-center mb-14">
            <p className="editorial-label mb-3">Nuestras tiendas</p>
            <h2 className="section-title">Explora por marca</h2>
          </div>
        </RevealOnScroll>

        <StaggerContainer
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
          staggerDelay={0.15}
        >
          {stores.map((store) => (
            <StaggerItem key={store.name}>
              <Link
                to={`/catalog?store=${store.slug}`}
                className="group editorial-card card-shadow block"
              >
                <div className="relative aspect-[4/5] overflow-hidden">
                  <img
                    src={store.image}
                    alt={store.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-editorial-black/50 via-editorial-black/10 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-6">
                    <p className="text-[10px] tracking-[0.3em] uppercase text-white/60 mb-1">
                      {store.description}
                    </p>
                    <h3 className="text-2xl font-display font-semibold text-white">
                      {store.name}
                    </h3>
                  </div>
                </div>
              </Link>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </section>

      {/* NEWSLETTER */}
      <section className="bg-editorial-black text-white py-20 md:py-28">
        <div className="max-w-[1400px] mx-auto px-5 sm:px-8 text-center">
          <RevealOnScroll>
            <p className="editorial-label text-white/40 mb-4">
              Mantente al dia
            </p>
            <h2 className="section-title text-white mb-4">
              Unete al estilo
            </h2>
            <p className="text-white/50 max-w-md mx-auto mb-8">
              Recibe primero las nuevas colecciones, descuentos exclusivos y
              tips de estilo directo en tu correo.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="tu@email.com"
                className="w-full sm:flex-1 bg-white/10 border border-white/10 rounded-full px-6 py-3 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-white/30 transition-colors"
              />
              <button className="w-full sm:w-auto btn-gradient">
                Suscribirme
              </button>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-editorial-black border-t border-white/5 py-12">
        <div className="max-w-[1400px] mx-auto px-5 sm:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <span className="text-[13px] font-display italic font-semibold tracking-[0.15em] text-white/60">
                FT. THE LINE ONE
              </span>
            </div>
            <div className="flex items-center gap-8">
              {["Catalogo", "Try-On IA", "Tiendas"].map((link) => (
                <Link
                  key={link}
                  to={
                    link === "Catalogo"
                      ? "/catalog"
                      : link === "Try-On IA"
                      ? "/virtual-try-on"
                      : "/catalog"
                  }
                  className="text-xs text-white/40 hover:text-white/70 transition-colors tracking-wide"
                >
                  {link}
                </Link>
              ))}
            </div>
            <p className="text-[11px] text-white/20">
              &copy; 2026 FT. THE LINE ONE. Todos los derechos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Home;
