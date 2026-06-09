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
  logout: () => void;
  refresh: () => Promise<void>;
}

const UserAuthContext = createContext<UserAuthContextType | null>(null);

export function UserAuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const clearSession = () => {
    localStorage.removeItem("user_token");
    setUser(null);
  };

  const refresh = async () => {
    const token = localStorage.getItem("user_token");
    if (!token) {
      setUser(null);
      return;
    }
    api.setUserToken(token);
    const me = await api.getMe();
    setUser(me);
  };

  useEffect(() => {
    const token = localStorage.getItem("user_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api.setUserToken(token);
    api.getMe()
      .then(setUser)
      .catch(() => clearSession())
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const { access_token } = await api.login(username, password);
    localStorage.setItem("user_token", access_token);
    api.setUserToken(access_token);
    const me = await api.getMe();
    if (me.role === "super_admin") {
      clearSession();
      throw new Error("Для владельца сайта — отдельный вход в личную панель");
    }
    setUser(me);
    return me;
  };

  const logout = () => {
    api.setUserToken(null);
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
