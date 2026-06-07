import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";

export function Settings() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Настройки</h2>
        <p className="text-muted-foreground">Конфигурация системы</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Профиль</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p><strong>Логин:</strong> {user?.username}</p>
          <p><strong>Имя:</strong> {user?.full_name || "—"}</p>
          <p><strong>Email:</strong> {user?.email || "—"}</p>
          <p><strong>Роль:</strong> {user?.role}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Интеграции</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="font-medium">ВКонтакте Bot</p>
              <p className="text-muted-foreground">Приём обращений через VK Callback API</p>
            </div>
            <span className="text-xs text-muted-foreground">Настраивается через .env</span>
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="font-medium">Gemini AI</p>
              <p className="text-muted-foreground">Анализ и классификация обращений</p>
            </div>
            <span className="text-xs text-muted-foreground">GEMINI_API_KEY</span>
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div>
              <p className="font-medium">Telegram</p>
              <p className="text-muted-foreground">Уведомления ответственным</p>
            </div>
            <span className="text-xs text-muted-foreground">TELEGRAM_BOT_TOKEN</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
