import { Link } from "react-router-dom";
import { QUICK_NAV_EXTRA, QUICK_NAV_SECTIONS } from "@/lib/navigation";

const links = [...QUICK_NAV_SECTIONS, ...QUICK_NAV_EXTRA];

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
