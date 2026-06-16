import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, User } from "@/lib/api";
import { initVkBridge, resolveSilentAuthPayload, setVkViewportHeight } from "@/lib/vkBridge";

const VK_TOKEN_KEY = "vk_mini_app_token";

interface VkAuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  refreshAuth: () => Promise<void>;
  logout: () => void;
}

const VkAuthContext = createContext<VkAuthContextValue | null>(null);

export function VkAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applySession = useCallback((accessToken: string, profile: User) => {
    sessionStorage.setItem(VK_TOKEN_KEY, accessToken);
    api.setUserToken(accessToken);
    setToken(accessToken);
    setUser(profile);
    setError(null);
  }, []);

  const clearSession = useCallback(() => {
    sessionStorage.removeItem(VK_TOKEN_KEY);
    api.setUserToken(null);
    setToken(null);
    setUser(null);
  }, []);

  const refreshAuth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await initVkBridge();
      setVkViewportHeight();
      const payload = await resolveSilentAuthPayload();
      const auth = await api.vkAuth(payload);
      applySession(auth.access_token, auth.user);
    } catch (err) {
      clearSession();
      setError(err instanceof Error ? err.message : "Не удалось войти через VK");
    } finally {
      setLoading(false);
    }
  }, [applySession, clearSession]);

  useEffect(() => {
    const saved = sessionStorage.getItem(VK_TOKEN_KEY);
    if (saved) {
      api.setUserToken(saved);
      setToken(saved);
      api
        .getMe()
        .then((me) => {
          setUser(me);
          setLoading(false);
        })
        .catch(() => {
          void refreshAuth();
        });
      return;
    }
    void refreshAuth();
  }, [refreshAuth]);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      error,
      refreshAuth,
      logout: clearSession,
    }),
    [user, token, loading, error, refreshAuth, clearSession],
  );

  return <VkAuthContext.Provider value={value}>{children}</VkAuthContext.Provider>;
}

export function useVkAuth() {
  const ctx = useContext(VkAuthContext);
  if (!ctx) throw new Error("useVkAuth must be used inside VkAuthProvider");
  return ctx;
}
