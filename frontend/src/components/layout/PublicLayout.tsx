import { useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { PushkinBanner } from "@/components/PushkinBanner";

const nav = [
  { to: "/", label: "Главная" },
  { to: "/ai", label: "ИИ" },
  { to: "/map", label: "Карта" },
  { to: "/services", label: "Услуги" },
  { to: "/classifieds", label: "Объявления" },
  { to: "/services/cabinet", label: "Кабинет мастера" },
];

export function PublicLayout() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-screen feather-pattern flex flex-col">
      <header className="pushkin-gradient text-white shadow-xl sticky top-0 z-50">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 md:px-6 md:py-4">
          <Link to="/" className="flex items-center gap-3">
            <span className="text-3xl">🪶</span>
            <div>
              <h1 className="text-lg md:text-xl font-bold leading-tight">Народный Контроль</h1>
              <p className="text-xs text-amber-200/90">Пушкинские Горы</p>
            </div>
          </Link>
          <button className="md:hidden text-2xl p-2" onClick={() => setMenuOpen(!menuOpen)} aria-label="Меню">
            ☰
          </button>
          <nav className="hidden md:flex gap-5">
            {nav.map(({ to, label }) => (
              <Link key={to} to={to} className="text-sm text-white/90 transition hover:text-amber-300 font-medium">
                {label}
              </Link>
            ))}
            <Link to="/admin/login" className="text-sm text-amber-300/80 hover:text-amber-200">Вход</Link>
          </nav>
        </div>
        {menuOpen && (
          <nav className="md:hidden border-t border-white/10 px-4 py-3 flex flex-col gap-2">
            {nav.map(({ to, label }) => (
              <Link key={to} to={to} className="py-2 text-white/90" onClick={() => setMenuOpen(false)}>{label}</Link>
            ))}
          </nav>
        )}
      </header>

      <PushkinBanner />

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="pushkin-footer mt-auto">
        <div className="mx-auto max-w-6xl px-4 py-10 text-center">
          <p className="font-serif italic text-lg text-amber-900/90 leading-relaxed">
            «Здесь Пушкин родился, здесь он и умер,<br />
            <span className="text-base">как волк неволен, как птица не сво вольна...»</span>
          </p>
          <p className="mt-4 text-sm text-emerald-900/70">
            Народный Контроль — Пушкинские Горы · {new Date().getFullYear()}
          </p>
          <p className="mt-2 text-xs text-emerald-800/50">
            Земля поэта · Псковская область
          </p>
        </div>
      </footer>
    </div>
  );
}
