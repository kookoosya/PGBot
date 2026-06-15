import { Link } from "react-router-dom";
import { LiterarySectionHead } from "@/components/literary";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";

const usefulItems = [
  { icon: "🗺", title: "Карта", desc: "Магазины, НКЦ, такси и маршруты", to: "/map", tone: "forest" as const },
  { icon: "📋", title: "Объявления", desc: "Дрова, услуги, продажа — от соседей", to: "/classifieds", tone: "gold" as const },
  { icon: "📅", title: "Афиша", desc: "События и кино в регионе", to: "/events", tone: "gold" as const },
  { icon: "🤖", title: "ИИ-помощник", desc: "Тексты, идеи, ответы о посёлке", to: "/ai", tone: "forest" as const },
  { icon: "🛠", title: "Услуги", desc: "Мастера, покос, дрова, ремонт", to: "/services", tone: "forest" as const },
  { icon: "⚠️", title: "Обращения", desc: "Дороги, ЖКХ, освещение", to: "/complaints", tone: "gold" as const },
];

export function LandingUsefulNearby() {
  const copy = LANDING_SECTIONS.useful;

  return (
    <div className="page-panel page-panel--gold landing-block">
      <LiterarySectionHead
        kicker={copy.kicker}
        title={copy.title}
        lead={copy.lead}
      />
      <div className="literary-useful-grid">
        {usefulItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`literary-useful-card literary-useful-card--${item.tone}`}
          >
            <span className="literary-useful-icon">{item.icon}</span>
            <h3 className="literary-useful-title">{item.title}</h3>
            <p className="literary-useful-desc">{item.desc}</p>
            <span className="literary-useful-go">Открыть →</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
