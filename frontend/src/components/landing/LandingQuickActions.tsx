import { Link } from "react-router-dom";
import { LiterarySectionHead } from "@/components/literary";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";

const ACTIONS = [
  { to: "/classifieds?new=1", label: "Подать объявление", icon: "✍️" },
  { to: "/complaints", label: "Обращение в администрацию", icon: "⚠️" },
  { to: "/map", label: "Справочник на карте", icon: "🗺" },
] as const;

/** Три частых действия — не дублирует вкладки навигации. */
export function LandingQuickActions() {
  const copy = LANDING_SECTIONS.useful;

  return (
    <nav className="page-panel page-panel--gold landing-block" aria-label="Быстрые действия">
      <LiterarySectionHead title={copy.title} lead={copy.lead} compact />
      <div className="landing-quick-nav landing-quick-nav--actions">
        {ACTIONS.map((item) => (
          <Link key={item.to} to={item.to} className="landing-quick-nav-item no-underline">
            <span className="landing-quick-nav-icon" aria-hidden>
              {item.icon}
            </span>
            <span className="landing-quick-nav-label">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
