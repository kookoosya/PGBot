import { Link } from "react-router-dom";

const links = [
  { to: "/", label: "Главная", icon: "🏠" },
  { to: "/map", label: "Карта", icon: "🗺" },
  { to: "/classifieds", label: "Объявления", icon: "📋" },
  { to: "/services", label: "Услуги", icon: "💇" },
  { to: "/ai", label: "ИИ", icon: "🤖" },
  { to: "/cabinet", label: "Кабинет", icon: "👤" },
  { to: "/register", label: "Регистрация", icon: "✍️" },
];

export function FooterNav() {
  return (
    <nav className="footer-nav" aria-label="Навигация в подвале">
      {links.map(({ to, label, icon }) => (
        <Link key={to} to={to} className="footer-nav-link">
          <span>{icon}</span>
          {label}
        </Link>
      ))}
    </nav>
  );
}
