import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, Issue } from "@/lib/api";
import { formatDate, STATUS_COLORS, STATUS_LABELS } from "@/lib/utils";

const STATUSES = ["NEW", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED"];

export function Issues() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Issue | null>(null);

  const loadIssues = () => {
    const params: Record<string, string> = { page: String(page), page_size: "20" };
    if (statusFilter) params.status_filter = statusFilter;
    if (search) params.search = search;
    api.getIssues(params).then((r) => {
      setIssues(r.items);
      setTotal(r.total);
    }).catch(console.error);
  };

  useEffect(() => { loadIssues(); }, [page, statusFilter]);

  const handleStatusChange = async (issue: Issue, status: string) => {
    await api.updateIssueStatus(issue.id, status);
    loadIssues();
    if (selected?.id === issue.id) {
      setSelected(await api.getIssue(issue.id));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Обращения</h2>
        <p className="text-muted-foreground">Управление обращениями жителей</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          className="h-10 rounded-md border px-3 text-sm"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">Все статусы</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{STATUS_LABELS[s]}</option>
          ))}
        </select>
        <input
          className="h-10 rounded-md border px-3 text-sm"
          placeholder="Поиск..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && loadIssues()}
        />
        <Button onClick={loadIssues} size="sm">Найти</Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-3">
          {issues.map((issue) => (
            <Card
              key={issue.id}
              className={`cursor-pointer transition-shadow hover:shadow-md ${selected?.id === issue.id ? "ring-2 ring-primary" : ""}`}
              onClick={() => setSelected(issue)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">#{issue.id}</span>
                      <Badge className={STATUS_COLORS[issue.status]}>
                        {STATUS_LABELS[issue.status]}
                      </Badge>
                      {issue.category && (
                        <Badge className="bg-gray-100 text-gray-700">{issue.category}</Badge>
                      )}
                    </div>
                    <p className="mt-2 text-sm">{issue.ai_analysis?.summary || issue.description}</p>
                    {issue.address && (
                      <p className="mt-1 text-xs text-muted-foreground">📍 {issue.address}</p>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatDate(issue.created_at)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
          {issues.length === 0 && (
            <p className="text-center text-muted-foreground py-8">Обращения не найдены</p>
          )}
          <div className="flex justify-between">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
              Назад
            </Button>
            <span className="text-sm text-muted-foreground self-center">
              Стр. {page} из {Math.ceil(total / 20) || 1}
            </span>
            <Button variant="outline" size="sm" disabled={page * 20 >= total} onClick={() => setPage(page + 1)}>
              Далее
            </Button>
          </div>
        </div>

        {selected && (
          <Card className="h-fit sticky top-8">
            <CardHeader>
              <CardTitle>Обращение #{selected.id}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium">Описание</p>
                <p className="text-sm text-muted-foreground mt-1">{selected.description}</p>
              </div>
              {selected.ai_analysis && (
                <div className="rounded-md bg-muted p-3 text-sm space-y-1">
                  <p><strong>AI:</strong> {selected.ai_analysis.summary}</p>
                  <p>Категория: {selected.ai_analysis.category}</p>
                  <p>Приоритет: {selected.ai_analysis.priority}</p>
                  <p>Отдел: {selected.ai_analysis.suggested_department}</p>
                  {selected.ai_analysis.duplicate_probability != null && (
                    <p>Дубликат: {(selected.ai_analysis.duplicate_probability * 100).toFixed(0)}%</p>
                  )}
                </div>
              )}
              {selected.photos.length > 0 && (
                <div className="flex gap-2 flex-wrap">
                  {selected.photos.map((p) => (
                    <img key={p.id} src={p.url} alt="" className="h-20 w-20 rounded object-cover" />
                  ))}
                </div>
              )}
              <div>
                <p className="text-sm font-medium mb-2">Изменить статус</p>
                <div className="flex flex-wrap gap-2">
                  {STATUSES.map((s) => (
                    <Button
                      key={s}
                      size="sm"
                      variant={selected.status === s ? "default" : "outline"}
                      onClick={() => handleStatusChange(selected, s)}
                    >
                      {STATUS_LABELS[s]}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
