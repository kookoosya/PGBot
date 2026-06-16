import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { isVkMiniAppContext, readVkLaunchParams } from "@/lib/vkLaunchParams";

const VK_TOKEN_KEY = "vk_mini_app_token";

export function useVkMiniApp() {
  const [token, setToken] = useState<string | null>(() =>
    typeof window !== "undefined" ? sessionStorage.getItem(VK_TOKEN_KEY) : null,
  );
  const [loading, setLoading] = useState(isVkMiniAppContext());
  const [error, setError] = useState<string | null>(null);
  const inVk = isVkMiniAppContext();

  useEffect(() => {
    if (!inVk || token) {
      setLoading(false);
      return;
    }
    const launchParams = readVkLaunchParams();
    if (!launchParams) {
      setLoading(false);
      return;
    }
    api
      .vkMiniAppAuth(launchParams)
      .then((res) => {
        sessionStorage.setItem(VK_TOKEN_KEY, res.access_token);
        setToken(res.access_token);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Не удалось войти через VK");
      })
      .finally(() => setLoading(false));
  }, [inVk, token]);

  return { token, loading, error, inVk };
}
