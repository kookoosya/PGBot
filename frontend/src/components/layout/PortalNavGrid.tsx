import { Link } from "react-router-dom";
import { PORTAL_NAV_ITEMS, type NavSection } from "@/lib/navigation";

/** Единая сетка быстрой навигации по разделам портала. */
export function PortalNavGrid({
  className = "",
  prependItems = [],
}: {
  className?: string;
  prependItems?: NavSection[];
}) {
  const items = [...prependItems, ...PORTAL_NAV_ITEMS];

  return (
    <div className={`landing-quick-nav ${className}`.trim()}>
      {items.map((item) => (
        <Link key={item.to} to={item.to} className="landing-quick-nav-item no-underline">
          <span className="landing-quick-nav-icon" aria-hidden>{item.icon}</span>
          <span className="landing-quick-nav-label">{item.label}</span>
        </Link>
      ))}
    </div>
  );
}
