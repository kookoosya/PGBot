import { useEffect, useState } from "react";
import { ClassifiedMarketingCharts } from "@/components/ClassifiedMarketingCharts";
import { api, ClassifiedMarketingStats } from "@/lib/api";

export function AdminMarketing() {
  const [stats, setStats] = useState<ClassifiedMarketingStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getClassifiedMarketingStats()
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : "Ошибка загрузки"));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Статистика объявлений</h1>
        <p className="text-muted-foreground mt-1">
          Только для владельца — графики не показываются посетителям сайта.
        </p>
      </div>

      {error && <p className="text-destructive">{error}</p>}
      {stats && <ClassifiedMarketingCharts stats={stats} />}
      {!stats && !error && <p className="text-muted-foreground">Загрузка...</p>}
    </div>
  );
}
