import { useState, useCallback } from "react";
import { useSelector, useDispatch } from "react-redux";
import type { RootState, AppDispatch } from "@/store";
import { openUpgradeModal, closeUpgradeModal } from "@/store/uiSlice";

interface UseFeatureGateReturn {
  isPremium: boolean;
  showUpgrade: boolean;
  showUpgradeModal: () => void;
  hideUpgradeModal: () => void;
  handleUpgrade: () => Promise<void>;
  upgradeLoading: boolean;
  upgradeError: string | null;
  canUseVton: boolean;
  vtonRemaining: number;
}

export function useFeatureGate(): UseFeatureGateReturn {
  const dispatch = useDispatch<AppDispatch>();
  const { user } = useSelector((state: RootState) => state.user);
  const { upgradeModal } = useSelector((state: RootState) => state.ui);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [upgradeError, setUpgradeError] = useState<string | null>(null);

  const isPremium = user?.is_premium || user?.plan_type === "premium";
  const vtonUsed = user?.daily_usage?.vton || 0;
  const vtonLimit = isPremium ? Infinity : 5;
  const vtonRemaining = Math.max(0, vtonLimit - vtonUsed);
  const canUseVton = isPremium || vtonUsed < 5;

  const showUpgradeModalFn = useCallback(() => {
    dispatch(openUpgradeModal());
  }, [dispatch]);

  const hideUpgradeModalFn = useCallback(() => {
    dispatch(closeUpgradeModal());
    setUpgradeError(null);
  }, [dispatch]);

  const handleUpgrade = useCallback(async () => {
    setUpgradeLoading(true);
    setUpgradeError(null);
    try {
      // Redirect to profile subscription tab (payment flow lives there)
      window.location.href = "/profile#subscription";
    } catch (err: any) {
      setUpgradeError(err.message || "Error al procesar el pago");
    } finally {
      setUpgradeLoading(false);
    }
  }, []);

  return {
    isPremium,
    showUpgrade: upgradeModal.isOpen,
    showUpgradeModal: showUpgradeModalFn,
    hideUpgradeModal: hideUpgradeModalFn,
    handleUpgrade,
    upgradeLoading,
    upgradeError,
    canUseVton,
    vtonRemaining,
  };
}
