import { Link, Outlet } from "react-router-dom";
import { FooterNav } from "@/components/FooterNav";
import { PushkinBanner } from "@/components/PushkinBanner";
import { BRAND } from "@/lib/branding";
import { TabNav } from "./TabNav";

export function PublicLayout() {
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
            <Link to="/admin/login" className="pushkin-login-btn">
              Вход для служб
            </Link>
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
          <FooterNav />
          <p className="pushkin-quote-footer mt-8">
            «Здесь Пушкин родился, здесь он и умер...»
          </p>
          <p className="pushkin-footer-line">
            {BRAND.name} · {BRAND.district} · {new Date().getFullYear()}
          </p>
          <p className="pushkin-footer-note">Сервис «{BRAND.programName}» для жителей посёлка</p>
        </div>
      </footer>
    </div>
  );
}
