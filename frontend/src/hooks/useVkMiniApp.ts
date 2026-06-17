import { useEffect, useState } from "react";
import { api } from "@/lib/api/index";
import { initVkBridge, isVkMiniAppRuntime, readVkLaunchParamsAsync } from "@/lib/vkBridge";
import { useUserAuth } from "@/lib/userAuth";

export const VK_TOKEN_KEY = "vk_mini_app_token";

export function useVkMiniApp() {
  const { refresh } = useUserAuth();
  const [token, setToken] = useState<string | null>(() =>
    typeof window !== "undefined" ? sessionStorage.getItem(VK_TOKEN_KEY) : null,
  );
  const [loading, setLoading] = useState(isVkMiniAppRuntime());
  const [error, setError] = useState<string | null>(null);
  const inVk = isVkMiniAppRuntime();

  useEffect(() => {
    if (token) {
      api.setUserToken(token);
      void refresh();
      setLoading(false);
      return;
    }
    if (!inVk) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    (async () => {
      await initVkBridge();
      const launchParams = await readVkLaunchParamsAsync();
      if (cancelled) return;
      if (!launchParams) {
        setLoading(false);
        return;
      }
      try {
        const res = await api.vkMiniAppAuth(launchParams);
        if (cancelled) return;
        sessionStorage.setItem(VK_TOKEN_KEY, res.access_token);
        api.setUserToken(res.access_token);
        setToken(res.access_token);
        setError(null);
        await refresh();
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Не удалось войти через VK");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [inVk, token, refresh]);

  return { token, loading, error, inVk };
}
