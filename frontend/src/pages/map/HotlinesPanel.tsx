import { telHref } from "@/components/VkBotLink";
import { LiterarySectionHead } from "@/components/literary";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";

import { VILLAGE_HOTLINES } from "./hotlines";

export function HotlinesPanel() {
  const copy = PAGE_SECTIONS.map.hotlines;

  return (
    <div className="page-section pb-3">
      <div className="page-panel page-panel--gold hotlines-panel">
        <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />
        <div className="hotlines-grid">
          {VILLAGE_HOTLINES.map((h) => (
            <a
              key={`${h.name}-${h.phone}`}
              href={telHref(h.phone)}
              className={`hotline-card${h.emergency ? " hotline-card--emergency" : ""}`}
            >
              <span className="hotline-icon" aria-hidden>
                {h.icon}
              </span>
              <div className="hotline-body">
                <strong>{h.name}</strong>
                <p className="hotline-phone">{h.phone}</p>
                {h.note && <p className="hotline-note">{h.note}</p>}
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
