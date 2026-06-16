interface VkBackBarProps {
  title: string;
  onBack: () => void;
}

export function VkBackBar({ title, onBack }: VkBackBarProps) {
  return (
    <div className="vk-back-bar">
      <button type="button" className="vk-back-btn" onClick={onBack} aria-label="Назад">
        ← Назад
      </button>
      <h2 className="vk-back-title">{title}</h2>
    </div>
  );
}
