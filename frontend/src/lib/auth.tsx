import React, { createContext, useContext, useEffect, useState } from "react";
import { api, User } from "./api";

const OWNER_DENIED = "Личная панель только для владельца сайта";

interface AuthContextType {
  user: User | null;
  isOwner: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

async function verifyOwnerAccess(): Promise<void> {
  const me = await api.getMe();
  if (me.role !== "super_admin") {
    throw new Error(OWNER_DENIED);
  }
  await api.ownerCheck();
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(true);

  const clearSession = () => {
    localStorage.removeItem("token");
    api.setToken(null);
    setUser(null);
    setIsOwner(false);
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }

    api.setToken(token);
    api.getMe()
      .then(async (me) => {
        await api.ownerCheck();
        setUser(me);
        setIsOwner(true);
      })
      .catch(() => clearSession())
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const { access_token } = await api.login(username, password);
    localStorage.setItem("token", access_token);
    api.setToken(access_token);
    try {
      await verifyOwnerAccess();
      const me = await api.getMe();
      setUser(me);
      setIsOwner(true);
    } catch (err) {
      clearSession();
      throw err instanceof Error ? err : new Error(OWNER_DENIED);
    }
  };

  const logout = () => clearSession();

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
