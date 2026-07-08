import { useSelector, useDispatch } from "react-redux";
import { useCallback, useState } from "react";
import { createPayment, redirectToWebpay } from "../services/payments";

const LIMITS = { vton: 10, llm: 10 };

export function useFeatureGate() {
  const dispatch = useDispatch();
  const { user, dailyUsage } = useSelector((state) => state.user);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [upgradeError, setUpgradeError] = useState(null);

  const isPremium = user?.is_premium || user?.plan_type === "premium";

  const vtonUsed = dailyUsage?.vton || 0;
  const llmUsed = dailyUsage?.llm || 0;
  const vtonRemaining = isPremium ? Infinity : Math.max(0, LIMITS.vton - vtonUsed);
  const llmRemaining = isPremium ? Infinity : Math.max(0, LIMITS.llm - llmUsed);

  const canUseVton = isPremium || vtonUsed < LIMITS.vton;
  const canUseLlm = isPremium || llmUsed < LIMITS.llm;

  const getUsageColor = (used) => {
    if (used <= 6) return "green";
    if (used === 7) return "yellow";
    if (used === 8) return "orange";
    return "red";
  };

  const showUpgradeModal = useCallback(() => setShowUpgrade(true), []);
  const hideUpgradeModal = useCallback(() => setShowUpgrade(false), []);

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
    user,
    vtonUsed,
    llmUsed,
    vtonRemaining,
    llmRemaining,
    canUseVton,
    canUseLlm,
    getUsageColor,
    showUpgrade,
    showUpgradeModal,
    hideUpgradeModal,
    handleUpgrade,
    upgradeLoading,
    upgradeError,
    limits: LIMITS,
  };
}
