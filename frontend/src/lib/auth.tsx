import React, { createContext, useContext, useEffect, useState } from "react";
import { api, User } from "./api";

const OWNER_DENIED = "Личная панель только для владельца сайта";

interface AuthContextType {
  user: User | null;
  isOwner: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(true);

  const clearSession = () => {
    api.setToken(null);
    setUser(null);
    setIsOwner(false);
  };

  useEffect(() => {
    api.refreshAccessToken("admin")
      .then(async (restored) => {
        if (!restored) return;
        await api.ownerCheck();
        const me = await api.getMe();
        setUser(me);
        setIsOwner(true);
      })
      .catch(() => clearSession())
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const { access_token } = await api.login(username, password, "admin");
    api.setToken(access_token);
    try {
      await api.ownerCheck();
      const me = await api.getMe();
      setUser(me);
      setIsOwner(true);
    } catch (err) {
      await api.logoutAuth("admin");
      clearSession();
      throw err instanceof Error ? err : new Error(OWNER_DENIED);
    }
  };

  const logout = async () => {
    await api.logoutAuth("admin");
    clearSession();
  };

  return (
    <AuthContext.Provider value={{ user, isOwner, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
