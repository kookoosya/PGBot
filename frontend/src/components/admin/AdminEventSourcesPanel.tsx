import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api/index";
import type { EventSourceHealth, EventSourceOverviewItem, EventSyncResult } from "@/lib/api/types/events";
import { formatSyncAge } from "@/lib/formatSyncAge";

function healthLabel(health: EventSourceHealth): string {
  if (health === "ready") return "Готов";
  return "Нужен токен";
}

function healthClass(health: EventSourceHealth): string {
  if (health === "ready") return "event-source-health event-source-health--ready";
  return "event-source-health event-source-health--bad";
}

export function canSyncEventSource(source: EventSourceOverviewItem): boolean {
  return source.health !== "needs_token";
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
  onFilterSource?: (sourceId: string) => void;
}

export function AdminEventSourcesPanel({ onSynced, onFilterSource }: AdminEventSourcesPanelProps) {
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

  const tokenAlerts = useMemo(() => {
    const sources = overview?.sources ?? [];
    return sources.filter((source) => source.health === "needs_token");
  }, [overview?.sources]);

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

        {!loading && tokenAlerts.length > 0 && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
            <p>
              <strong>{tokenAlerts.length}</strong>{" "}
              {tokenAlerts.length === 1 ? "источник" : "источника"} без токена:{" "}
              {tokenAlerts.map((source) => source.label).join(", ")}.
            </p>
            <p className="mt-1 text-amber-900/90">
              Инструкция: <code className="text-xs">docs/EVENT_SOURCES.md</code>, VK — шаг 8 в{" "}
              <code className="text-xs">docs/VK_SETUP.md</code>.
            </p>
          </div>
        )}

        {msg && <p className="text-sm text-green-700">{msg}</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="overflow-x-auto">
          <table className="admin-event-sources w-full text-sm">
            <thead>
              <tr>
                <th className="text-left py-2 pr-3">Источник</th>
                <th className="text-left py-2 pr-3">Статус</th>
                <th className="text-left py-2 pr-3">Обновление</th>
                <th className="text-right py-2 pr-3">В афише</th>
                <th className="text-right py-2">Действие</th>
              </tr>
            </thead>
            <tbody>
              {(overview?.sources ?? []).map((source) => {
                const syncable = canSyncEventSource(source);
                return (
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
                    <td className="py-2 pr-3 align-top text-muted-foreground text-xs">
                      {formatSyncAge(source.last_synced_at)}
                    </td>
                    <td className="py-2 pr-3 align-top text-right tabular-nums">
                      {onFilterSource && source.published_count > 0 ? (
                        <button
                          type="button"
                          className="admin-event-sources__count-link"
                          onClick={() => onFilterSource(source.id)}
                        >
                          {source.published_count}
                        </button>
                      ) : (
                        source.published_count
                      )}
                    </td>
                    <td className="py-2 align-top text-right">
                      {source.id !== "manual" ? (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={!!syncing || loading || !syncable}
                          title={!syncable ? source.token_hint ?? "Нужен токен" : undefined}
                          onClick={() => runSync(source.id)}
                        >
                          {syncing === source.id ? "…" : "Синк"}
                        </Button>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
