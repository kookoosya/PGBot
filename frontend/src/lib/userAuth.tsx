import React, { createContext, useContext, useEffect, useState } from "react";
import { api, User } from "./api";

const OFFICIAL_ROLES = ["administration", "social_service", "moderator"];

export function isOfficialUser(user: User | null | undefined): boolean {
  return !!user && OFFICIAL_ROLES.includes(user.role);
}

interface UserAuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const UserAuthContext = createContext<UserAuthContextType | null>(null);

export function UserAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const clearSession = () => {
    api.setUserToken(null);
    setUser(null);
  };

  const refresh = async () => {
    const restored = await api.refreshAccessToken("user");
    if (!restored) {
      clearSession();
      return;
    }
    const me = await api.getMe();
    setUser(me);
  };

  useEffect(() => {
    api.refreshAccessToken("user")
      .then(async (restored) => {
        if (!restored) return;
        const me = await api.getMe();
        setUser(me);
      })
      .catch(() => clearSession())
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const { access_token } = await api.login(username, password, "user");
    api.setUserToken(access_token);
    const me = await api.getMe();
    if (me.role === "super_admin") {
      await api.logoutAuth("user");
      clearSession();
      throw new Error("Для владельца сайта — отдельный вход в личную панель");
    }
    setUser(me);
    return me;
  };

  const logout = async () => {
    await api.logoutAuth("user");
    clearSession();
  };

  return (
    <UserAuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </UserAuthContext.Provider>
  );
}

export function useUserAuth() {
  const ctx = useContext(UserAuthContext);
  if (!ctx) throw new Error("useUserAuth must be used within UserAuthProvider");
  return ctx;
}
