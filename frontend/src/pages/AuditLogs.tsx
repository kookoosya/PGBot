import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { api, AuditLog } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    api.getAuditLogs().then(setLogs).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Аудит</h2>
        <p className="text-muted-foreground">Журнал действий администрации</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="p-4 text-left font-medium">Дата</th>
                <th className="p-4 text-left font-medium">Пользователь</th>
                <th className="p-4 text-left font-medium">Действие</th>
                <th className="p-4 text-left font-medium">Объект</th>
                <th className="p-4 text-left font-medium">Детали</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b">
                  <td className="p-4 text-muted-foreground whitespace-nowrap">
                    {formatDate(log.created_at)}
                  </td>
                  <td className="p-4">{log.user || "—"}</td>
                  <td className="p-4 font-medium">{log.action}</td>
                  <td className="p-4">{log.entity_type} #{log.entity_id}</td>
                  <td className="p-4 text-muted-foreground text-xs max-w-xs truncate">
                    {log.details ? JSON.stringify(log.details) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && (
            <p className="text-center text-muted-foreground py-8">Записей пока нет</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
