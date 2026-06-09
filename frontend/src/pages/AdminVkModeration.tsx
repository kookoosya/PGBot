import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { api, VkModerationLog, VkModerationState } from "@/lib/api";

export function AdminVkModeration() {
  const [states, setStates] = useState<VkModerationState[]>([]);
  const [logs, setLogs] = useState<VkModerationLog[]>([]);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    api
      .getVkModeration()
      .then((data) => {
        setStates(data.states);
        setLogs(data.recent_logs);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Ошибка загрузки"));
  };

  useEffect(() => {
    load();
  }, []);

  const unblock = async (vkUserId: number) => {
    setMsg("");
    setError("");
    try {
      await api.unblockVkUser(vkUserId);
      setMsg(`Пользователь VK ${vkUserId} разблокирован`);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось разблокировать");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Модерация VK-бота</h1>
        <p className="text-muted-foreground mt-1">
          Автоматические предупреждения (5) и блокировка на 7 дней. Ручная разблокировка ниже.
        </p>
      </div>

      {msg && <p className="text-green-700">{msg}</p>}
      {error && <p className="text-destructive">{error}</p>}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Пользователи с предупреждениями</h2>
        {states.length === 0 ? (
          <p className="text-muted-foreground text-sm">Нарушений пока нет.</p>
        ) : (
          states.map((state) => (
            <div key={state.vk_user_id} className="pushkin-card p-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold">VK ID: {state.vk_user_id}</p>
                <p className="text-sm text-muted-foreground">
                  Предупреждений: {state.warning_count}
                  {state.banned_until && ` · Блок до ${new Date(state.banned_until).toLocaleString("ru-RU")}`}
                </p>
              </div>
              <Button size="sm" variant="outline" onClick={() => unblock(state.vk_user_id)}>
                Разблокировать
              </Button>
            </div>
          ))
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Журнал нарушений</h2>
        <div className="overflow-x-auto">
          <table className="pushkin-table w-full">
            <thead>
              <tr>
                <th>Время</th>
                <th>VK ID</th>
                <th>Причина</th>
                <th>Действие</th>
                <th>Сообщение</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.created_at).toLocaleString("ru-RU")}</td>
                  <td>{log.vk_user_id}</td>
                  <td>{log.reason}</td>
                  <td>{log.action} (#{log.warning_number})</td>
                  <td className="max-w-xs truncate">{log.message_excerpt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
