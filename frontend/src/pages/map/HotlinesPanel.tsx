import { telHref } from "@/components/VkBotLink";
import { LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";

import { EMERGENCY_HOTLINES } from "./hotlines";
import type { VerifiedPhoneContactsState } from "./useVerifiedPhoneContacts";

type HotlinesPanelProps = {
  compact?: boolean;
  contacts: VerifiedPhoneContactsState;
};

function PhoneCard({
  icon,
  name,
  phone,
  note,
  website,
  emergency,
}: {
  icon: string;
  name: string;
  phone: string;
  note?: string | null;
  website?: string | null;
  emergency?: boolean;
}) {
  return (
    <a
      href={telHref(phone)}
      className={`hotline-card${emergency ? " hotline-card--emergency" : ""}`}
    >
      <span className="hotline-icon" aria-hidden>
        {icon}
      </span>
      <div className="hotline-body">
        <strong>{name}</strong>
        <p className="hotline-phone">{phone}</p>
        {note && <p className="hotline-note">{note}</p>}
        {website && (
          <p className="hotline-note">
            <span>{website.replace(/^https?:\/\//, "")}</span>
          </p>
        )}
      </div>
    </a>
  );
}

export function HotlinesPanel({ compact = false, contacts }: HotlinesPanelProps) {
  const copy = PAGE_SECTIONS.map.hotlines;
  const { groups, loading, error } = contacts;

  return (
    <div className={compact ? "hotlines-compact" : "page-section pb-3"}>
      <div className={`page-panel page-panel--gold hotlines-panel${compact ? " hotlines-panel-compact" : ""}`}>
        {!compact && (
          <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />
        )}

        <section className="phone-contact-section" aria-label="Экстренные номера">
          <h4 className="phone-contact-section-title">Экстренные</h4>
          <div className="hotlines-grid">
            {EMERGENCY_HOTLINES.map((h) => (
              <PhoneCard
                key={`${h.name}-${h.phone}`}
                icon={h.icon}
                name={h.name}
                phone={h.phone}
                note={h.note}
                emergency
              />
            ))}
          </div>
        </section>

        {loading && (
          <div className="p-3">
            <LiteraryInlineLoader label="Загружаем номера…" />
          </div>
        )}

        {error && !loading && (
          <p className="text-sm text-muted-foreground px-1 mt-3">
            Не удалось загрузить номера организаций. Попробуйте обновить страницу.
          </p>
        )}

        {!loading &&
          !error &&
          groups.map((group) => (
            <section key={group.title} className="phone-contact-section" aria-label={group.title}>
              <h4 className="phone-contact-section-title">{group.title}</h4>
              <div className="hotlines-grid">
                {group.items.map((entry) => (
                  <PhoneCard
                    key={entry.id}
                    icon={entry.icon}
                    name={entry.name}
                    phone={entry.phone}
                    note={entry.note}
                    website={entry.website}
                  />
                ))}
              </div>
            </section>
          ))}
      </div>
    </div>
  );
}
