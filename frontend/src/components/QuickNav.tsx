import { Link } from "react-router-dom";

const links = [
  { to: "/map", icon: "🗺", label: "Карта", desc: "Магазины и службы" },
  { to: "/classifieds", icon: "📋", label: "Объявления", desc: "От жителей" },
  { to: "/services", icon: "💇", label: "Услуги", desc: "Мастера посёлка" },
  { to: "/ai", icon: "🤖", label: "ИИ", desc: "Помощник" },
];

export function QuickNav() {
  return (
    <div className="quick-nav-grid">
      {links.map(({ to, icon, label, desc }) => (
        <Link key={to} to={to} className="quick-nav-card">
          <span className="quick-nav-icon">{icon}</span>
          <span className="quick-nav-label">{label}</span>
          <span className="quick-nav-desc">{desc}</span>
        </Link>
      ))}
    </div>
  );
}
