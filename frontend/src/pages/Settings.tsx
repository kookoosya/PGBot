import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

export function Settings() {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (newPassword !== confirmPassword) {
      setPasswordError("Новые пароли не совпадают");
      return;
    }

    setSaving(true);
    try {
      const result = await api.changePassword(currentPassword, newPassword);
      setPasswordSuccess(result.message);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Не удалось сменить пароль");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Настройки</h2>
        <p className="text-muted-foreground">Ваш личный аккаунт владельца</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Профиль</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p><strong>Логин:</strong> {user?.username}</p>
          <p><strong>Имя:</strong> {user?.full_name || "—"}</p>
          <p><strong>Email:</strong> {user?.email || "—"}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Смена пароля</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordChange} className="max-w-md space-y-4">
            <div>
              <label className="text-sm font-medium">Текущий пароль</label>
              <Input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Новый пароль</label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Повторите новый пароль</label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>
            {passwordError && <p className="text-sm text-destructive">{passwordError}</p>}
            {passwordSuccess && <p className="text-sm text-green-600">{passwordSuccess}</p>}
            <Button type="submit" disabled={saving}>
              {saving ? "Сохранение..." : "Обновить пароль"}
            </Button>
          </form>
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
