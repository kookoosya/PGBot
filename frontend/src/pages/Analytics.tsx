import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, Statistics } from "@/lib/api";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function Analytics() {
  const [stats, setStats] = useState<Statistics | null>(null);

  useEffect(() => {
    api.getStatistics().then(setStats).catch(console.error);
  }, []);

  if (!stats) return <p className="text-muted-foreground">Загрузка...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold">Аналитика</h2>
        <p className="text-muted-foreground">Статистика обращений жителей</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {[
          { label: "Всего", value: stats.total_issues },
          { label: "Решено", value: stats.resolved_issues },
          { label: "В работе", value: stats.in_progress_issues },
          { label: "Ср. время (ч)", value: stats.avg_resolution_hours ?? "—" },
        ].map(({ label, value }) => (
          <Card key={label}>
            <CardContent className="pt-6 text-center">
              <p className="text-2xl font-bold">{value}</p>
              <p className="text-sm text-muted-foreground">{label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Топ категорий</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stats.top_categories}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="hsl(221.2, 83.2%, 53.3%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Динамика по месяцам</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={stats.monthly_dynamics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" name="Всего" stroke="hsl(221.2, 83.2%, 53.3%)" />
                <Line type="monotone" dataKey="resolved" name="Решено" stroke="hsl(142, 76%, 36%)" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {stats.top_streets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Проблемные адреса</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">Адрес</th>
                  <th className="p-2 text-right">Обращений</th>
                </tr>
              </thead>
              <tbody>
                {stats.top_streets.map((s) => (
                  <tr key={s.street} className="border-b">
                    <td className="p-2">{s.street}</td>
                    <td className="p-2 text-right font-medium">{s.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
