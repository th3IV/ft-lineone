import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink, Clock, CheckCircle, AlertCircle, Loader, Trash2, Download } from "lucide-react";
import api from "../services/api";
import { deleteVtonResult } from "../services/vton";
import toast from "react-hot-toast";

function VtonHistory() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState(null);
  const [deleting, setDeleting] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await api.get("/vton/history?limit=50");
      setResults(res.data.results || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle size={14} className="text-green-500" />;
      case "processing":
      case "pending":
        return <Loader size={14} className="text-amber-500 animate-spin" />;
      case "failed":
        return <AlertCircle size={14} className="text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "completed": return "Completado";
      case "processing": return "Procesando";
      case "pending": return "Pendiente";
      case "failed": return "Fallido";
      default: return status;
    }
  };

  const handleDelete = async (e, resultId) => {
    e.stopPropagation();
    setDeleting(resultId);
    try {
      await deleteVtonResult(resultId);
      setResults(results.filter((r) => r.id !== resultId));
      if (selectedResult?.id === resultId) setSelectedResult(null);
      toast.success("Resultado eliminado");
    } catch {
      toast.error("Error al eliminar");
    } finally {
      setDeleting(null);
    }
  };

  const handleDownload = (e, imageUrl, productName) => {
    e.stopPropagation();
    const a = document.createElement("a");
    a.href = imageUrl;
    a.download = `vton-${productName || "resultado"}.jpg`;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="w-8 h-8 rounded-full border-2 border-editorial-black/10 border-t-editorial-black animate-spin" />
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-16">
        <Clock size={40} className="mx-auto text-editorial-gray-light mb-4" />
        <p className="text-editorial-gray text-sm">
          Todavia no tienes pruebas virtuales. Prueba una prenda para ver el resultado aqui.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((result) => (
          <motion.div
            key={result.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="editorial-card card-shadow overflow-hidden cursor-pointer group"
            onClick={() => setSelectedResult(result)}
          >
            {/* Image comparison */}
            <div className="relative aspect-[3/4] bg-editorial-cream-dark">
              {result.status === "completed" && result.output_image_url ? (
                <img
                  src={result.output_image_url}
                  alt="Resultado VTON"
                  className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500"
                />
              ) : result.input_image_url ? (
                <img
                  src={result.input_image_url}
                  alt="Foto de entrada"
                  className="w-full h-full object-cover opacity-60"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Clock size={32} className="text-editorial-gray-light" />
                </div>
              )}

              {/* Status overlay */}
              <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-editorial-white/90 backdrop-blur-sm rounded-full px-2.5 py-1">
                {getStatusIcon(result.status)}
                <span className="text-[10px] font-medium">{getStatusLabel(result.status)}</span>
              </div>

              {/* Action buttons */}
              <div className="absolute top-3 right-3 flex gap-1.5 z-10">
                {result.output_image_url && (
                  <button
                    onClick={(e) => handleDownload(e, result.output_image_url, result.product?.name)}
                    className="w-7 h-7 rounded-full bg-editorial-white/90 backdrop-blur-sm flex items-center justify-center hover:bg-editorial-white transition-colors"
                    title="Descargar"
                  >
                    <Download size={12} className="text-editorial-black" />
                  </button>
                )}
                <button
                  onClick={(e) => handleDelete(e, result.id)}
                  disabled={deleting === result.id}
                  className="w-7 h-7 rounded-full bg-editorial-white/90 backdrop-blur-sm flex items-center justify-center hover:bg-red-50 transition-colors disabled:opacity-50"
                  title="Eliminar"
                >
                  {deleting === result.id ? (
                    <Loader size={12} className="text-red-500 animate-spin" />
                  ) : (
                    <Trash2 size={12} className="text-red-500" />
                  )}
                </button>
              </div>
            </div>

            {/* Info */}
            <div className="p-3">
              {result.product && (
                <p className="text-xs font-medium text-editorial-black truncate">
                  {result.product.name}
                </p>
              )}
              <p className="text-[10px] text-editorial-gray mt-0.5">
                {new Date(result.created_at).toLocaleDateString("es-CL", {
                  day: "numeric",
                  month: "short",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedResult && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setSelectedResult(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-editorial-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-editorial-black/5">
                <div>
                  <h3 className="font-display font-semibold text-sm">
                    {selectedResult.product?.name || "Resultado VTON"}
                  </h3>
                  <p className="text-[10px] text-editorial-gray mt-0.5">
                    {new Date(selectedResult.created_at).toLocaleDateString("es-CL", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedResult(null)}
                  className="w-8 h-8 rounded-full hover:bg-editorial-cream flex items-center justify-center transition-colors"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Image */}
              <div className="aspect-[3/4] sm:aspect-video bg-editorial-cream-dark">
                {selectedResult.status === "completed" && selectedResult.output_image_url ? (
                  <img
                    src={selectedResult.output_image_url}
                    alt="Resultado VTON"
                    className="w-full h-full object-contain"
                  />
                ) : selectedResult.input_image_url ? (
                  <img
                    src={selectedResult.input_image_url}
                    alt="Foto de entrada"
                    className="w-full h-full object-contain opacity-60"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <p className="text-editorial-gray text-sm">Imagen no disponible</p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(selectedResult.status)}
                  <span className="text-xs">{getStatusLabel(selectedResult.status)}</span>
                </div>
                <div className="flex items-center gap-2">
                  {selectedResult.output_image_url && (
                    <button
                      onClick={(e) => handleDownload(e, selectedResult.output_image_url, selectedResult.product?.name)}
                      className="btn-outline text-xs flex items-center gap-1.5"
                    >
                      <Download size={12} />
                      Descargar
                    </button>
                  )}
                  <button
                    onClick={(e) => handleDelete(e, selectedResult.id)}
                    disabled={deleting === selectedResult.id}
                    className="btn-outline text-xs flex items-center gap-1.5 hover:bg-red-50 hover:border-red-200 disabled:opacity-50"
                  >
                    <Trash2 size={12} className="text-red-500" />
                    Eliminar
                  </button>
                  {selectedResult.product?.original_url && (
                    <a
                      href={selectedResult.product.original_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-outline text-xs flex items-center gap-1.5"
                    >
                      <ExternalLink size={12} />
                      Ver prenda
                    </a>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default VtonHistory;
