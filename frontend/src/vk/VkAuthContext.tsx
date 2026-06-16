import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { api, User } from "@/lib/api";
import { initVkBridge, resolveSilentAuthPayload, setVkViewportHeight } from "@/lib/vkBridge";
import { vkAuthErrorMessage } from "@/vk/lib/errors";

const VK_TOKEN_KEY = "vk_mini_app_token";

interface VkAuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  refreshAuth: () => Promise<void>;
  ensureSession: () => Promise<boolean>;
  logout: () => void;
}

const VkAuthContext = createContext<VkAuthContextValue | null>(null);

export function VkAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const reauthInFlight = useRef<Promise<boolean> | null>(null);

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

  const exchangeSilentToken = useCallback(async (): Promise<boolean> => {
    await initVkBridge();
    setVkViewportHeight();
    const payload = await resolveSilentAuthPayload();
    const auth = await api.vkRefresh(payload);
    applySession(auth.access_token, auth.user);
    return true;
  }, [applySession]);

  const refreshAuth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await exchangeSilentToken();
    } catch (err) {
      clearSession();
      setError(vkAuthErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [clearSession, exchangeSilentToken]);

  const ensureSession = useCallback(async (): Promise<boolean> => {
    if (reauthInFlight.current) return reauthInFlight.current;

    const task = (async () => {
      try {
        await exchangeSilentToken();
        return true;
      } catch {
        clearSession();
        setError("Сессия истекла. Нажмите «Войти снова» на вкладке «Заявки».");
        return false;
      } finally {
        reauthInFlight.current = null;
      }
    })();

    reauthInFlight.current = task;
    return task;
  }, [clearSession, exchangeSilentToken]);

  useEffect(() => {
    api.setUnauthorizedHandler(ensureSession);
    return () => api.setUnauthorizedHandler(null);
  }, [ensureSession]);

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
      ensureSession,
      logout: clearSession,
    }),
    [user, token, loading, error, refreshAuth, ensureSession, clearSession],
  );

  return <VkAuthContext.Provider value={value}>{children}</VkAuthContext.Provider>;
}

export function useVkAuth() {
  const ctx = useContext(VkAuthContext);
  if (!ctx) throw new Error("useVkAuth must be used inside VkAuthProvider");
  return ctx;
}
