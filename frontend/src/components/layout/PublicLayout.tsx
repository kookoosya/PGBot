import { Link, Outlet } from "react-router-dom";

const nav = [
  { to: "/", label: "Главная" },
  { to: "/ai", label: "ИИ-помощник" },
  { to: "/map", label: "Карта" },
  { to: "/services", label: "Услуги" },
  { to: "/register", label: "Регистрация служб" },
  { to: "/admin/login", label: "Вход" },
];

export function PublicLayout() {
  return (
    <div className="min-h-screen feather-pattern">
      <header className="pushkin-gradient text-white shadow-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3">
            <span className="text-3xl">🪶</span>
            <div>
              <h1 className="text-xl font-bold leading-tight">Народный Контроль</h1>
              <p className="text-xs text-white/70">Пушкинские Горы</p>
            </div>
          </Link>
          <nav className="hidden gap-6 md:flex">
            {nav.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className="text-sm text-white/80 transition hover:text-amber-300"
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="border-t bg-card/50 py-8 text-center text-sm text-muted-foreground">
        <p className="font-serif italic">
          «Здесь Пушкин родился, здесь он и умер...»
        </p>
        <p className="mt-2">© {new Date().getFullYear()} Народный Контроль — Пушкинские Горы</p>
      </footer>
    </div>
  );
}
