import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type VkInfo = {
  vk_url: string;
  vk_bot_ready: boolean;
  vk_bot_hint: string;
};

export function telHref(phone: string): string {
  const digits = phone.replace(/[^\d+]/g, "");
  return digits ? `tel:${digits}` : "";
}

export function VkBotLink() {
  return <VkBotBanner compact />;
}

export function VkBotBanner({ compact = false }: { compact?: boolean }) {
  const [info, setInfo] = useState<VkInfo | null>(null);

  useEffect(() => {
    api
      .getPublicInfo()
      .then((i) =>
        setInfo({
          vk_url: i.vk_url,
          vk_bot_ready: i.vk_bot_ready ?? false,
          vk_bot_hint: i.vk_bot_hint ?? "",
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
    <a href={href} target="_blank" rel="noopener noreferrer" className="vk-cta-card">
      <span className="vk-cta-icon">📱</span>
      <div>
        <h3 className="vk-cta-title">
          {ready ? "ВК-бот посёлка — напишите «Начать»" : "ВК-бот — обращения жителей"}
        </h3>
        <p className="vk-cta-desc">
          {ready
            ? "Объявления, работа, жалобы с фото, маршруты, ИИ и подписка на новые объявления — в личных сообщениях сообщества."
            : info.vk_bot_hint ||
              "Откройте сообщения сообщества ВК и напишите «Начать». Ссылка настраивается владельцем портала."}
        </p>
        {!ready && (
          <p className="vk-cta-desc mt-2 opacity-70">
            Владельцу: укажите <code className="text-xs">VK_GROUP_URL</code> в настройках сервера — ссылка на ваше сообщество.
          </p>
        )}
      </div>
      <span className="vk-cta-arrow">→</span>
    </a>
  );
}
