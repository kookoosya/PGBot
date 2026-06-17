import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api, EventSourceOverviewItem, EventSyncResult } from "@/lib/api";

function healthLabel(health: EventSourceOverviewItem["health"]): string {
  if (health === "ready") return "Готов";
  if (health === "group_token_only") return "Только своя группа";
  return "Нужен токен";
}

function healthClass(health: EventSourceOverviewItem["health"]): string {
  if (health === "ready") return "event-source-health event-source-health--ready";
  if (health === "group_token_only") return "event-source-health event-source-health--warn";
  return "event-source-health event-source-health--bad";
}

function formatSyncSummary(results: EventSyncResult[]): string {
  return results
    .map((result) => {
      const prefix = result.source && result.source !== "unknown" ? `${result.source}: ` : "";
      if (result.errors.length) return `${prefix}${result.errors[0]}`;
      const region = result.region === "pskov" ? "Псков" : result.region === "pushkin_gory" ? "ПГ" : "все";
      return `${prefix}${region} +${result.created} / ~${result.updated}`;
    })
    .join(" · ");
}

interface AdminEventSourcesPanelProps {
  onSynced?: () => void;
}

export function AdminEventSourcesPanel({ onSynced }: AdminEventSourcesPanelProps) {
  const [overview, setOverview] = useState<Awaited<ReturnType<typeof api.getAdminEventSources>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    api
      .getAdminEventSources()
      .then(setOverview)
      .catch((err) => setError(err instanceof Error ? err.message : "Не удалось загрузить источники"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const runSync = async (source: string | "all") => {
    setSyncing(source);
    setMsg("");
    setError("");
    try {
      const results = source === "all" ? await api.syncAllEventSources() : await api.syncEventSource(source);
      setMsg(formatSyncSummary(results));
      load();
      onSynced?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Синхронизация не удалась");
    } finally {
      setSyncing(null);
    }
  };

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Источники афиши</h2>
            <p className="text-sm text-muted-foreground mt-1">
              {loading
                ? "Загружаем статистику…"
                : `Опубликовано событий: ${overview?.total_published ?? 0}`}
            </p>
          </div>
          <Button
            variant="outline"
            disabled={!!syncing || loading}
            onClick={() => runSync("all")}
          >
            {syncing === "all" ? "Синхронизация…" : "Синхронизировать всё"}
          </Button>
        </div>

        {msg && <p className="text-sm text-green-700">{msg}</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="overflow-x-auto">
          <table className="admin-event-sources w-full text-sm">
            <thead>
              <tr>
                <th className="text-left py-2 pr-3">Источник</th>
                <th className="text-left py-2 pr-3">Статус</th>
                <th className="text-right py-2 pr-3">В афише</th>
                <th className="text-right py-2">Действие</th>
              </tr>
            </thead>
            <tbody>
              {(overview?.sources ?? []).map((source) => (
                <tr key={source.id} className="border-t border-border/60">
                  <td className="py-2 pr-3 align-top">
                    <div className="font-medium">{source.label}</div>
                    {source.token_hint && (
                      <div className="text-xs text-muted-foreground mt-0.5 max-w-md">{source.token_hint}</div>
                    )}
                  </td>
                  <td className="py-2 pr-3 align-top">
                    <span className={healthClass(source.health)}>{healthLabel(source.health)}</span>
                  </td>
                  <td className="py-2 pr-3 align-top text-right tabular-nums">{source.published_count}</td>
                  <td className="py-2 align-top text-right">
                    {source.id !== "manual" ? (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={!!syncing || loading}
                        onClick={() => runSync(source.id)}
                      >
                        {syncing === source.id ? "…" : "Синк"}
                      </Button>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
