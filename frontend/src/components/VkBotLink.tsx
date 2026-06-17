import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api/index";
type PortalLinks = {
  home: string;
  complaints: string;
  classifieds: string;
  events: string;
  cabinet: string;
  map: string;
};

type VkInfo = {
  vk_url: string;
  vk_bot_ready: boolean;
  vk_bot_hint: string;
  portal_links?: PortalLinks;
};

const PORTAL_CHIPS: { key: keyof PortalLinks; label: string; icon: string }[] = [
  { key: "complaints", label: "Обращения", icon: "⚠️" },
  { key: "classifieds", label: "Объявления", icon: "📋" },
  { key: "events", label: "Афиша", icon: "📅" },
  { key: "cabinet", label: "Кабинет", icon: "🪶" },
];

function portalPath(url: string): string {
  try {
    const parsed = new URL(url);
    return `${parsed.pathname}${parsed.search}`;
  } catch {
    return url;
  }
}

export function telHref(phone: string): string {
  const digits = phone.replace(/[^\d+]/g, "");
  return digits ? `tel:${digits}` : "";
}

export function VkBotLink() {
  return <VkBotBanner compact />;
}

export function VkBotBanner({ compact = false, hidePortalChips = false }: { compact?: boolean; hidePortalChips?: boolean }) {
  const [info, setInfo] = useState<VkInfo | null>(null);

  useEffect(() => {
    api
      .getPublicInfo()
      .then((i) =>
        setInfo({
          vk_url: i.vk_url,
          vk_bot_ready: i.vk_bot_ready ?? false,
          vk_bot_hint: i.vk_bot_hint ?? "",
          portal_links: i.portal_links as PortalLinks | undefined,
        }),
      )
      .catch(() => {});
  }, []);

  if (!info) return null;

  const ready = info.vk_bot_ready;
  const href = info.vk_url;

  if (compact) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="pushkin-header-link pushkin-header-link-accent"
        title={info.vk_bot_hint}
      >
        📱 ВК-бот
      </a>
    );
  }

  return (
    <div className="vk-cta-wrap">
      <a href={href} target="_blank" rel="noopener noreferrer" className="vk-cta-card">
        <span className="vk-cta-icon">📱</span>
        <div>
          <h3 className="vk-cta-title">
            {ready ? "ВК-бот посёлка — напишите «Начать»" : "ВК-бот — обращения жителей"}
          </h3>
          <p className="vk-cta-desc">
            {ready
              ? "Объявления, работа, обращения с фото, маршруты, ИИ и подписка — в личных сообщениях сообщества."
              : info.vk_bot_hint ||
                "Откройте сообщения сообщества ВК и напишите «Начать». Ссылка настраивается владельцем портала."}
          </p>
        </div>
        <span className="vk-cta-arrow">→</span>
      </a>

      {info.portal_links && !hidePortalChips && (
        <div className="vk-portal-chips" aria-label="Разделы портала">
          <p className="vk-portal-chips-label">На сайте то же самое:</p>
          <div className="vk-portal-chips-row">
            {PORTAL_CHIPS.map((chip) => {
              const url = info.portal_links?.[chip.key];
              if (!url) return null;
              return (
                <Link key={chip.key} to={portalPath(url)} className="vk-portal-chip no-underline">
                  {chip.icon} {chip.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
