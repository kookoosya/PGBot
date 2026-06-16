interface VkSkeletonProps {
  lines?: number;
  className?: string;
}

export function VkSkeletonLine({ className = "" }: { className?: string }) {
  return <div className={`vk-skeleton-line ${className}`.trim()} aria-hidden />;
}

export function VkSkeletonCard({ lines = 3 }: VkSkeletonProps) {
  return (
    <div className="vk-skeleton-card" aria-busy="true" aria-label="Загрузка…">
      <VkSkeletonLine className="vk-skeleton-line--title" />
      {Array.from({ length: lines }, (_, i) => (
        <VkSkeletonLine key={i} className={i === lines - 1 ? "vk-skeleton-line--short" : ""} />
      ))}
    </div>
  );
}

export function VkSkeletonList({ count = 4 }: { count?: number }) {
  return (
    <div className="vk-skeleton-list">
      {Array.from({ length: count }, (_, i) => (
        <VkSkeletonCard key={i} lines={2} />
      ))}
    </div>
  );
}

export function VkSkeletonDetail() {
  return (
    <div className="vk-skeleton-detail" aria-busy="true" aria-label="Загрузка…">
      <VkSkeletonLine className="vk-skeleton-line--hero" />
      <VkSkeletonLine className="vk-skeleton-line--title" />
      <VkSkeletonLine />
      <VkSkeletonLine />
      <VkSkeletonLine className="vk-skeleton-line--short" />
    </div>
  );
}
