import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, Issue, Statistics } from "@/lib/api";
import { formatDate, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";
import { AlertCircle, CheckCircle, Clock, FileText } from "lucide-react";

export function Dashboard() {
  const [stats, setStats] = useState<Statistics | null>(null);
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);

  useEffect(() => {
    api.getStatistics().then(setStats).catch(console.error);
    api.getIssues({ page_size: "5" }).then((r) => setRecentIssues(r.items)).catch(console.error);
  }, []);

  const cards = [
    { title: "Всего обращений", value: stats?.total_issues ?? "—", icon: FileText, color: "text-blue-600" },
    { title: "Решено", value: stats?.resolved_issues ?? "—", icon: CheckCircle, color: "text-green-600" },
    { title: "В работе", value: stats?.in_progress_issues ?? "—", icon: Clock, color: "text-orange-600" },
    { title: "Отклонено", value: stats?.rejected_issues ?? "—", icon: AlertCircle, color: "text-red-600" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Обзор системы народного контроля</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map(({ title, value, icon: Icon, color }) => (
          <Card key={title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{title}</CardTitle>
              <Icon className={`h-4 w-4 ${color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {stats?.avg_resolution_hours != null && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              Среднее время решения: <strong>{stats.avg_resolution_hours} ч.</strong>
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Последние обращения</CardTitle>
          <Link to="/issues" className="text-sm text-primary hover:underline">
            Все обращения →
          </Link>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {recentIssues.map((issue) => (
              <div key={issue.id} className="flex items-center justify-between rounded-md border p-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">#{issue.id}</span>
                    <Badge className={STATUS_COLORS[issue.status]}>
                      {STATUS_LABELS[issue.status]}
                    </Badge>
                    {issue.is_spam && <Badge className="bg-red-100 text-red-800">Спам</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
                    {issue.ai_analysis?.summary || issue.description}
                  </p>
                </div>
                <span className="text-xs text-muted-foreground">{formatDate(issue.created_at)}</span>
              </div>
            ))}
            {recentIssues.length === 0 && (
              <p className="text-center text-muted-foreground py-4">Обращений пока нет</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
