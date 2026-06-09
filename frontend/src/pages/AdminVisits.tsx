import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, VisitStats } from "@/lib/api";

export function AdminVisits() {
  const [stats, setStats] = useState<VisitStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getVisitStats()
      .then(setStats)
      .catch((err) => setError(err instanceof Error ? err.message : "Ошибка"));
  }, []);

  if (error) return <p className="text-destructive">{error}</p>;
  if (!stats) return <p className="text-muted-foreground">Загрузка...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Посещения сайта</h1>
        <p className="text-muted-foreground mt-1">Только для владельца — считаются просмотры страниц</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Сегодня", value: stats.today, sub: `${stats.unique_today} уник.` },
          { label: "7 дней", value: stats.week, sub: `${stats.unique_week} уник.` },
          { label: "30 дней", value: stats.month, sub: "" },
          { label: "Всего", value: stats.total, sub: "" },
        ].map(({ label, value, sub }) => (
          <div key={label} className="pushkin-card p-5 text-center">
            <p className="text-3xl font-bold">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
            {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
          </div>
        ))}
      </div>

      <div className="marketing-chart-card">
        <h3 className="marketing-chart-title">Просмотры по дням (30 дней)</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={stats.daily}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="visits" name="Просмотры" fill="hsl(152 48% 28%)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="marketing-chart-card">
        <h3 className="marketing-chart-title">Популярные страницы (30 дней)</h3>
        <div className="space-y-2">
          {stats.top_pages.length === 0 && (
            <p className="text-sm text-muted-foreground">Пока нет данных — зайдите на сайт с телефона или компьютера</p>
          )}
          {stats.top_pages.map((p) => (
            <div key={p.path} className="flex justify-between items-center text-sm border-b pb-2">
              <span>{p.label}</span>
              <strong>{p.count}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
