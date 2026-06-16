import { Link } from "react-router-dom";
import { LiterarySectionHead } from "@/components/literary";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";

const NAV_ITEMS = [
  { icon: "🗺", title: "Карта", to: "/map" },
  { icon: "📅", title: "Афиша", to: "/events" },
  { icon: "📋", title: "Объявления", to: "/classifieds" },
  { icon: "💼", title: "Работа", to: "/jobs" },
  { icon: "🛠", title: "Услуги", to: "/services" },
  { icon: "⚠️", title: "Обращения", to: "/complaints" },
  { icon: "🤖", title: "ИИ", to: "/ai" },
  { icon: "🪶", title: "Кабинет", to: "/cabinet" },
] as const;

/** Компактная навигация по разделам — без дублирования hero-кнопок. */
export function LandingQuickNav() {
  const copy = LANDING_SECTIONS.useful;

  return (
    <nav className="page-panel page-panel--gold landing-block" aria-label="Разделы портала">
      <LiterarySectionHead kicker={copy.kicker} title={copy.title} compact />
      <div className="landing-quick-nav">
        {NAV_ITEMS.map((item) => (
          <Link key={item.to} to={item.to} className="landing-quick-nav-item no-underline">
            <span className="landing-quick-nav-icon" aria-hidden>{item.icon}</span>
            <span className="landing-quick-nav-label">{item.title}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
