import { useEffect, useState } from "react";
import { api, FeedbackItem } from "@/lib/api";

export function AdminFeedback() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    api.getAdminFeedback().then((r) => {
      setItems(r.items);
      setTotal(r.total);
    }).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold m-0">Пожелания жителей</h2>
        <p className="text-muted-foreground mt-1">Всего: {total}</p>
      </div>
      <div className="space-y-3">
        {items.length === 0 && (
          <div className="pushkin-card p-8 text-center text-muted-foreground">Пока нет пожеланий</div>
        )}
        {items.map((item) => (
          <div key={item.id} className="pushkin-card p-5">
            <div className="flex flex-wrap justify-between gap-2 text-xs text-muted-foreground mb-2">
              <span>#{item.id} · {new Date(item.created_at).toLocaleString("ru-RU")}</span>
              {item.page && <span>страница: {item.page}</span>}
            </div>
            <p className="whitespace-pre-wrap m-0">{item.message}</p>
            {item.contact && (
              <p className="text-sm mt-3 mb-0">
                <strong>Контакт:</strong> {item.contact}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
