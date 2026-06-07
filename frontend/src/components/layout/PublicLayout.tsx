import { useEffect } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { api } from "@/lib/api";
import { VkBotLink } from "@/components/VkBotLink";
import { BRAND } from "@/lib/branding";
import { useUserAuth } from "@/lib/userAuth";
import { TabNav } from "./TabNav";

export function PublicLayout() {
  const { user } = useUserAuth();
  const location = useLocation();

  useEffect(() => {
    api.trackVisit(location.pathname).catch(() => {});
  }, [location.pathname]);

  return (
    <div className="pushkin-page min-h-screen flex flex-col">
      <header className="pushkin-header-shell">
        <div className="pushkin-header">
          <div className="pushkin-header-row">
            <Link to="/" className="pushkin-brand">
              <div className="pushkin-logo-badge">🪶</div>
              <div>
                <p className="pushkin-brand-eyebrow">Портал посёлка</p>
                <h1 className="pushkin-brand-title">{BRAND.name}</h1>
              </div>
            </Link>
            <div className="pushkin-header-actions">
              <VkBotLink />
              {user ? (
                <Link to="/cabinet" className="pushkin-header-link">
                  👤 {user.full_name || user.username}
                </Link>
              ) : (
                <>
                  <Link to="/cabinet/login" className="pushkin-header-link">Вход</Link>
                  <Link to="/register" className="pushkin-header-link pushkin-header-link-accent">Регистрация</Link>
                </>
              )}
            </div>
          </div>
        </div>
        <TabNav variant="top" />
      </header>

      <main className="flex-1 w-full pushkin-main">
        <Outlet />
      </main>

      <footer className="pushkin-footer pushkin-footer-spacer">
        <div className="pushkin-footer-inner">
          <p className="pushkin-footer-line">
            {BRAND.name} · {BRAND.district} · {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  );
}
