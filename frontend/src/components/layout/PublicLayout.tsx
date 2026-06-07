import { useEffect } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { api } from "@/lib/api";
import { FooterNav } from "@/components/FooterNav";
import { PushkinBanner } from "@/components/PushkinBanner";
import { VkBotBanner, VkBotLink } from "@/components/VkBotLink";
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

      <PushkinBanner />

      <main className="flex-1 w-full pushkin-main">
        <Outlet />
      </main>

      <TabNav variant="bottom" />

      <footer className="pushkin-footer pushkin-footer-spacer">
        <div className="pushkin-footer-inner">
          <div className="mb-6">
            <VkBotBanner />
          </div>
          <FooterNav />
          <p className="pushkin-quote-footer mt-8">
            «Здесь Пушкин родился, здесь он и умер...»
          </p>
          <p className="pushkin-footer-line">
            {BRAND.name} · {BRAND.district} · {new Date().getFullYear()}
          </p>
          <p className="pushkin-footer-note">Сервис «{BRAND.programName}» для жителей посёлка</p>
          <p className="pushkin-footer-note mt-2 opacity-40">
            <Link to="/admin/login" className="hover:opacity-80">·</Link>
          </p>
        </div>
      </footer>
    </div>
  );
}
