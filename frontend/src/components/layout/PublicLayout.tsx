import { Link, Outlet } from "react-router-dom";
import { PushkinBanner } from "@/components/PushkinBanner";
import { TabNav } from "./TabNav";

export function PublicLayout() {
  return (
    <div className="pushkin-page min-h-screen flex flex-col">
      <header className="pushkin-header-shell">
        <div className="pushkin-header">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="pushkin-logo-badge">🪶</div>
              <div>
                <h1 className="text-lg font-bold text-amber-100 leading-tight tracking-wide">
                  Народный Контроль
                </h1>
                <p className="text-xs text-amber-300 font-medium">Пушкинские Горы</p>
              </div>
            </Link>
            <Link to="/admin/login" className="pushkin-login-btn text-sm">
              Вход
            </Link>
          </div>
        </div>
        <TabNav variant="top" />
      </header>

      <PushkinBanner />

      <main className="flex-1 mx-auto w-full max-w-6xl px-3 md:px-6 py-4 pushkin-main">
        <Outlet />
      </main>

      <TabNav variant="bottom" />

      <footer className="pushkin-footer pushkin-footer-spacer">
        <div className="mx-auto max-w-6xl px-4 py-8 text-center">
          <p className="pushkin-quote-footer">
            «Здесь Пушкин родился, здесь он и умер...»
          </p>
          <p className="mt-3 text-sm font-medium text-amber-950">
            Народный Контроль — Пушкинские Горы · {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  );
}
