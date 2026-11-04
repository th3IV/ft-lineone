import { useState, useCallback } from "react";

const AD_COOLDOWN_MS = 5 * 60 * 1000; // 5 min between ads

export function useRewardedAd() {
  const [adCompleted, setAdCompleted] = useState(false);
  const [adLoading, setAdLoading] = useState(false);

  const canShowAd = useCallback(() => {
    const lastAd = localStorage.getItem("lastRewardedAd");
    if (!lastAd) return true;
    return Date.now() - parseInt(lastAd, 10) > AD_COOLDOWN_MS;
  }, []);

  const showAd = useCallback(() => {
    if (!canShowAd()) {
      setAdCompleted(true);
      return Promise.resolve(true);
    }

    setAdLoading(true);

    // Check if GPT is loaded
    if (typeof window.googletag !== "undefined" && window.googletag.apiReady) {
      return new Promise((resolve) => {
        const slot = window.googletag
          .defineOutOfPageSlot(
            "/233474685,22904221008/FT_BANNER_INTERSTITIAL",
            window.googletag.enums.OutOfPageFormat.INTERSTITIAL
          )
          .setTargeting("type", ["rewarded"])
          .addService(window.googletag.pubads());

        window.googletag.pubads().addEventListener("slotRenderEnded", (e) => {
          if (e.slot === slot) {
            setAdLoading(false);
            setAdCompleted(true);
            localStorage.setItem("lastRewardedAd", Date.now().toString());
            resolve(true);
          }
        });

        window.googletag.enableServices();
        window.googletag.display(slot);
      });
    }

    // Fallback: simulate ad if GPT not loaded (dev / no ad account yet)
    return new Promise((resolve) => {
      setTimeout(() => {
        setAdLoading(false);
        setAdCompleted(true);
        localStorage.setItem("lastRewardedAd", Date.now().toString());
        resolve(true);
      }, 1500);
    });
  }, [canShowAd]);

  const reset = useCallback(() => {
    setAdCompleted(false);
    setAdLoading(false);
  }, []);

  return { adCompleted, adLoading, showAd, reset, canShowAd: canShowAd() };
}
