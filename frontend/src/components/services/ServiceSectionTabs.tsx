import { SERVICE_TABS, type ServiceTabId } from "@/lib/servicesBoard";

type ServiceSectionTabsProps = {
  active: ServiceTabId;
  onChange: (tab: ServiceTabId) => void;
  counts?: Partial<Record<ServiceTabId, number>>;
};

export function ServiceSectionTabs({ active, onChange, counts }: ServiceSectionTabsProps) {
  return (
    <nav className="classified-board-tabs" aria-label="Разделы услуг">
      {SERVICE_TABS.map((tab) => {
        const count = counts?.[tab.id];
        return (
          <button
            key={tab.id}
            type="button"
            className={`classified-board-tab${active === tab.id ? " classified-board-tab--active" : ""}`}
            onClick={() => onChange(tab.id)}
            aria-current={active === tab.id ? "page" : undefined}
          >
            <span className="classified-board-tab-icon" aria-hidden>
              {tab.icon}
            </span>
            <span className="classified-board-tab-label">
              {tab.title}
              {count != null && count > 0 ? ` (${count})` : ""}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
