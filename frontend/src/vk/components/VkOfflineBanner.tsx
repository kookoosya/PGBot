interface VkOfflineBannerProps {
  online: boolean;
}

export function VkOfflineBanner({ online }: VkOfflineBannerProps) {
  if (online) return null;
  return (
    <div className="vk-offline-banner" role="status">
      Нет интернета — данные могут быть устаревшими
    </div>
  );
}
