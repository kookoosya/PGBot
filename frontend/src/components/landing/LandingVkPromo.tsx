import { useEffect, useState } from "react";
import { api } from "@/lib/api/index";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";

const copy = LANDING_SECTIONS.vk;

/** Компактное промо ВК-бота на главной — без дублирования табов. */
export function LandingVkPromo() {
  const [vkUrl, setVkUrl] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api
      .getPublicInfo()
      .then((info) => {
        setVkUrl(info.vk_url);
        setReady(info.vk_bot_ready ?? false);
      })
      .catch(() => {});
  }, []);

  if (!vkUrl) return null;

  return (
    <section className="page-panel page-panel--forest landing-block landing-vk-promo" aria-label="ВКонтакте">
      <a href={vkUrl} target="_blank" rel="noopener noreferrer" className="landing-vk-promo-link no-underline">
        <span className="landing-vk-promo-icon" aria-hidden>📱</span>
        <div>
          <p className="landing-vk-promo-title m-0">{copy.title}</p>
          <p className="landing-vk-promo-lead m-0">
            {ready ? copy.lead : "Напишите «Начать» в сообщениях сообщества ВК."}
          </p>
        </div>
        <span className="landing-vk-promo-arrow" aria-hidden>→</span>
      </a>
    </section>
  );
}
