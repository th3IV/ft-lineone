import { useSelector, useDispatch } from "react-redux";
import { useCallback, useState } from "react";
import { createPayment, redirectToWebpay } from "../services/payments";
import { openUpgradeModal, closeUpgradeModal } from "../store/uiSlice";

export function useFeatureGate() {
  const dispatch = useDispatch();
  const { user, dailyUsage } = useSelector((state) => state.user);
  const { upgradeModal } = useSelector((state) => state.ui);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [upgradeError, setUpgradeError] = useState(null);

  const isPremium = user?.is_premium || user?.plan_type === "premium";

  const limit = dailyUsage?.limit ?? 5;
  const isUnlimited = limit === -1 || isPremium;

  const vtonUsed = dailyUsage?.vton || 0;
  const llmUsed = dailyUsage?.llm || 0;
  const vtonRemaining = isUnlimited ? Infinity : Math.max(0, limit - vtonUsed);
  const llmRemaining = isUnlimited ? Infinity : Math.max(0, limit - llmUsed);

  const canUseVton = isUnlimited || vtonRemaining > 0;
  const canUseLlm = isUnlimited || llmRemaining > 0;

  const getUsageColor = (used) => {
    if (isUnlimited) return "green";
    if (used <= limit * 0.6) return "green";
    if (used <= limit * 0.7) return "yellow";
    if (used <= limit * 0.8) return "orange";
    return "red";
  };

  const showUpgradeModal = useCallback(() => dispatch(openUpgradeModal()), [dispatch]);
  const hideUpgradeModal = useCallback(() => dispatch(closeUpgradeModal()), [dispatch]);

  const handleUpgrade = useCallback(async () => {
    setUpgradeLoading(true);
    setUpgradeError(null);
    try {
      const data = await createPayment();
      if (data.url && data.token) {
        redirectToWebpay(data.url, data.token);
      } else {
        setUpgradeError("No se pudo crear la transaccion. Intenta nuevamente.");
      }
    } catch (err) {
      console.error("Payment error:", err);
      setUpgradeError("Error al conectar con la pasarela de pago. Intenta nuevamente.");
    } finally {
      setUpgradeLoading(false);
    }
  }, []);

  return {
    isPremium,
    isUnlimited,
    user,
    vtonUsed,
    llmUsed,
    vtonRemaining,
    llmRemaining,
    canUseVton,
    canUseLlm,
    getUsageColor,
    showUpgrade: upgradeModal.isOpen,
    showUpgradeModal,
    hideUpgradeModal,
    handleUpgrade,
    upgradeLoading,
    upgradeError,
    limit,
    limits: { vton: limit, llm: limit },
  };
}
