import { NavLink } from "react-router-dom";
import { MAIN_SECTIONS } from "@/lib/navigation";

export function TabNav({ variant = "top" }: { variant?: "top" | "bottom" }) {
  const isBottom = variant === "bottom";

  return (
    <nav
      className={
        isBottom
          ? "pushkin-tab-bar-bottom"
          : "pushkin-tab-bar-top pushkin-tab-bar-top-desktop"
      }
      aria-label="Навигация по разделам"
    >
      <div className="pushkin-tab-inner">
        <div className="pushkin-tab-scroll">
          {MAIN_SECTIONS.map(({ to, label, icon, end }) => (
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
