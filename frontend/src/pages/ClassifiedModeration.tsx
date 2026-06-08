import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { api, ClassifiedPending } from "@/lib/api";

export function ClassifiedModeration() {
  const [items, setItems] = useState<ClassifiedPending[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .getPendingClassifieds()
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const approve = async (id: number) => {
    await api.approveClassified(id);
    load();
  };

  const reject = async (id: number) => {
    await api.rejectClassified(id);
    load();
  };

  if (loading) return <p>Загрузка...</p>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">📋 Модерация объявлений</h2>
      <p className="text-sm text-muted-foreground mb-6">
        Размещение бесплатное — проверьте текст на мошенничество и опубликуйте
      </p>
      <div className="space-y-4">
        {items.map((ad) => (
          <div key={ad.id} className="pushkin-card p-5">
            <div className="flex justify-between items-start gap-4">
              <div>
                <h3 className="font-bold text-lg">{ad.title}</h3>
                <p className="text-xs text-muted-foreground">
                  {ad.category_label} · {ad.author_name} · {ad.phone}
                </p>
                <p className="text-sm mt-2">{ad.description}</p>
                {ad.contact_vk && (
                  <p className="text-sm mt-2 text-blue-800">VK для уведомления: {ad.contact_vk}</p>
                )}
                {ad.address && <p className="text-xs mt-1 text-muted-foreground">📍 {ad.address}</p>}
                <p className="text-xs mt-2 text-muted-foreground">
                  {new Date(ad.created_at).toLocaleString("ru")}
                </p>
              </div>
              <div className="flex flex-col gap-2 shrink-0">
                <Button size="sm" onClick={() => approve(ad.id)}>
                  Опубликовать
                </Button>
                <Button size="sm" variant="outline" onClick={() => reject(ad.id)}>
                  Отклонить
                </Button>
              </div>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-muted-foreground">Нет объявлений на модерации</p>
        )}
      </div>
    </div>
  );
}
