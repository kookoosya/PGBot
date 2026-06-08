import { useEffect } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { PageBackdrop } from "@/components/PageBackdrop";
import { PushkinBanner } from "@/components/PushkinBanner";
import { FooterNav } from "@/components/FooterNav";
import { VkBotLink } from "@/components/VkBotLink";
import { api } from "@/lib/api";
import { BRAND } from "@/lib/branding";
import { getUserHomePath } from "@/lib/navigation";
import { useUserAuth } from "@/lib/userAuth";
import { TabNav } from "./TabNav";

export function PublicLayout() {
  const { user } = useUserAuth();
  const location = useLocation();
  const isHome = location.pathname === "/";

  useEffect(() => {
    api.trackVisit(location.pathname).catch(() => {});
  }, [location.pathname]);

  return (
    <div className="pushkin-page min-h-screen flex flex-col relative">
      <PageBackdrop />
      <div className="site-shell relative z-10 flex flex-col min-h-screen">
      <header className="pushkin-header-shell epic-header-shell">
        <div className="pushkin-header epic-header">
          <div className="pushkin-header-row">
            <Link to="/" className="pushkin-brand">
              <div className="pushkin-logo-badge">🪶</div>
              <div>
                <p className="pushkin-brand-eyebrow">{BRAND.tagline}</p>
                <h1 className="pushkin-brand-title">{BRAND.name}</h1>
              </div>
            </Link>
            <div className="pushkin-header-actions">
              {!isHome && <VkBotLink />}
              {user ? (
                <Link to={getUserHomePath(user)} className="pushkin-header-link">
                  👤 {user.full_name || user.username}
                </Link>
              ) : (
                <>
                  <Link to="/cabinet/login" className="pushkin-header-link">Вход</Link>
                  <Link to="/register" className="pushkin-header-link pushkin-header-link-accent">
                    Регистрация
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
        <TabNav variant="top" />
      </header>

      {!isHome && <PushkinBanner />}

      <main className="flex-1 w-full pushkin-main page-fade-wrap" key={location.pathname}>
        <Outlet />
      </main>

      <footer className="pushkin-footer pushkin-footer-spacer">
        <div className="pushkin-footer-inner">
          <FooterNav />
          <p className="pushkin-footer-line">
            {BRAND.name} · {BRAND.district} · {BRAND.programName} · {new Date().getFullYear()}
          </p>
        </div>
      </footer>

      <TabNav variant="bottom" />
      </div>
    </div>
  );
}
