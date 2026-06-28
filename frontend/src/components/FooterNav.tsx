import { useEffect, useState } from "react";
import { api } from "@/lib/api/index";
import { BRAND } from "@/lib/branding";

export function FooterNav() {
  const [vkUrl, setVkUrl] = useState<string | null>(null);

  useEffect(() => {
    api.getPublicInfo().then((info) => setVkUrl(info.vk_url)).catch(() => {});
  }, []);

  return (
    <div className="footer-nav" aria-label="Подвал">
      <p className="footer-nav-tagline m-0 text-sm text-muted-foreground">
        {BRAND.tagline} · {BRAND.district} · {new Date().getFullYear()}
      </p>
      {vkUrl && (
        <a
          href={vkUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="footer-nav-link no-underline mt-2 inline-flex items-center gap-1"
        >
          💬 То же во ВКонтакте — бот в сообщениях
        </a>
      )}
    </div>
  );
}
