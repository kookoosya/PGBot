import { useSiteInfo } from "@/hooks/useSiteInfo";

export function telHref(phone: string): string {
  const digits = phone.replace(/[^\d+]/g, "");
  return digits ? `tel:${digits}` : "";
}

export function VkBotLink({ className = "pushkin-header-link pushkin-header-link-accent" }: { className?: string }) {
  const { info } = useSiteInfo();
  if (!info?.vk_bot_ready || !/^https:\/\/(?:www\.)?(?:vk\.com|vk\.ru)\/[\w.-]+\/?$/i.test(info.vk_url)) return null;

  return (
    <a href={info.vk_url} target="_blank" rel="noopener noreferrer" className={className}>
      Бот ВКонтакте <span aria-hidden="true">↗</span>
    </a>
  );
}
