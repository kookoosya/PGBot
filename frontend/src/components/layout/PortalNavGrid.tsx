import { Link } from "react-router-dom";

export const PORTAL_NAV_ITEMS = [
  { icon: "🗺", title: "Карта", to: "/map" },
  { icon: "📅", title: "Афиша", to: "/events" },
  { icon: "📋", title: "Объявления", to: "/classifieds" },
  { icon: "💼", title: "Работа", to: "/jobs" },
  { icon: "🛠", title: "Услуги", to: "/services" },
  { icon: "⚠️", title: "Обращения", to: "/complaints" },
  { icon: "🤖", title: "ИИ", to: "/ai" },
  { icon: "🪶", title: "Кабинет", to: "/cabinet" },
] as const;

/** Единая сетка быстрой навигации по разделам портала. */
export function PortalNavGrid({ className = "" }: { className?: string }) {
  return (
    <div className={`landing-quick-nav ${className}`.trim()}>
      {PORTAL_NAV_ITEMS.map((item) => (
        <Link key={item.to} to={item.to} className="landing-quick-nav-item no-underline">
          <span className="landing-quick-nav-icon" aria-hidden>{item.icon}</span>
          <span className="landing-quick-nav-label">{item.title}</span>
        </Link>
      ))}
    </div>
  );
}
