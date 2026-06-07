import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ClassifiedMarketingStats } from "@/lib/api";

const ROI_COLORS = ["#b45309", "#15803d", "#1d4ed8", "#7c3aed"];

interface Props {
  stats: ClassifiedMarketingStats;
}

export function ClassifiedMarketingCharts({ stats }: Props) {
  return (
    <div className="marketing-section space-y-6">
      <div className="marketing-header">
        <h3 className="marketing-title">📈 Почему это выгодно</h3>
        <p className="marketing-subtitle">
          {stats.placement_fee} ₽ за объявление на {stats.period_days} дней — вы зарабатываете, сайт развивается
        </p>
      </div>

      <div className="marketing-stats-row">
        <div className="marketing-stat">
          <span className="marketing-stat-value">{stats.monthly_reach_estimate.toLocaleString("ru")}</span>
          <span className="marketing-stat-label">просмотров в месяц</span>
        </div>
        <div className="marketing-stat">
          <span className="marketing-stat-value">{stats.total_ads}</span>
          <span className="marketing-stat-label">активных объявлений</span>
        </div>
        <div className="marketing-stat">
          <span className="marketing-stat-value">{stats.avg_views_per_ad}</span>
          <span className="marketing-stat-label">ср. просмотров на объявление</span>
        </div>
      </div>

      <div className="marketing-charts-grid">
        <div className="marketing-chart-card">
          <h4 className="marketing-chart-title">Просмотры по дням недели</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.weekly_views}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(42 30% 85%)" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="views" name="Просмотры" fill="hsl(152 48% 28%)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="marketing-chart-card">
          <h4 className="marketing-chart-title">Окупаемость: 150 ₽ → доход</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.roi_examples} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(42 30% 85%)" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="service" width={90} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: number) => [`${v.toLocaleString("ru")} ₽`, "Доход"]} />
              <Bar dataKey="income" name="Доход" radius={[0, 6, 6, 0]}>
                {stats.roi_examples.map((_, i) => (
                  <Cell key={i} fill={ROI_COLORS[i % ROI_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="marketing-chart-note">
            Пример: маникюр — 4 клиента × 1200 ₽ = 4800 ₽. Вложили 150 ₽ — получили в 32 раза больше.
          </p>
        </div>
      </div>

      {stats.category_stats.length > 0 && (
        <div className="marketing-chart-card">
          <h4 className="marketing-chart-title">Популярные категории на портале</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.category_stats.slice(0, 6)}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(42 30% 85%)" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="ads" name="Объявлений" fill="hsl(42 78% 46%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
