import { NavLink } from "react-router-dom";

const tabs = [
  { to: "/", label: "Главная", icon: "🏠", end: true },
  { to: "/map", label: "Карта", icon: "🗺" },
  { to: "/classifieds", label: "Объявления", icon: "📋" },
  { to: "/services", label: "Услуги", icon: "💇" },
  { to: "/ai", label: "ИИ", icon: "🤖" },
  { to: "/services/cabinet", label: "Мастерам", icon: "📅" },
];

export function TabNav({ variant = "top" }: { variant?: "top" | "bottom" }) {
  const isBottom = variant === "bottom";

  return (
    <nav
      className={isBottom ? "pushkin-tab-bar-bottom" : "pushkin-tab-bar-top"}
      aria-label="Навигация по разделам"
    >
      <div className="pushkin-tab-inner">
        <div className="pushkin-tab-scroll">
          {tabs.map(({ to, label, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `pushkin-tab ${isActive ? "pushkin-tab-active" : ""}`
              }
            >
              <span className="pushkin-tab-icon" aria-hidden>
                {icon}
              </span>
              <span className="pushkin-tab-label">{label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
