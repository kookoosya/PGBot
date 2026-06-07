import { Link } from "react-router-dom";

const links = [
  { to: "/map", icon: "🗺", label: "Карта", desc: "Магазины и службы", color: "quick-nav-map" },
  { to: "/classifieds", icon: "📋", label: "Объявления", desc: "От жителей", color: "quick-nav-ads" },
  { to: "/services", icon: "💇", label: "Услуги", desc: "Мастера", color: "quick-nav-svc" },
  { to: "/ai", icon: "🤖", label: "ИИ", desc: "Помощник", color: "quick-nav-ai" },
  { to: "/services/cabinet", icon: "📅", label: "Мастер", desc: "Кабинет", color: "quick-nav-cab" },
  { to: "/services/register", icon: "✨", label: "Стать мастером", desc: "Регистрация", color: "quick-nav-reg" },
];

export function QuickNav() {
  return (
    <div className="quick-nav-grid quick-nav-grid-6">
      {links.map(({ to, icon, label, desc, color }) => (
        <Link key={to} to={to} className={`quick-nav-card ${color}`}>
          <span className="quick-nav-icon">{icon}</span>
          <span className="quick-nav-label">{label}</span>
          <span className="quick-nav-desc">{desc}</span>
          <span className="quick-nav-arrow" aria-hidden>→</span>
        </Link>
      ))}
    </div>
  );
}
