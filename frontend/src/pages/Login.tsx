import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";
import { BRAND } from "@/lib/branding";

export function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center pushkin-gradient feather-pattern px-4">
      <Card className="w-full max-w-md pushkin-card bg-card/95">
        <CardHeader className="text-center">
          <span className="text-4xl">🔐</span>
          <CardTitle className="text-2xl mt-2">{BRAND.adminTitle}</CardTitle>
          <p className="text-sm text-muted-foreground">
            {BRAND.name} · личный доступ владельца
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Логин</label>
              <Input value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="username" />
            </div>
            <div>
              <label className="text-sm font-medium">Пароль</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Проверка..." : "Войти в панель"}
            </Button>
          </form>
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Доступ только для владельца сайта. Временный вход: <strong>admin</strong> / <strong>admin</strong>
          </p>
          <div className="mt-4 text-center text-sm text-muted-foreground">
            <Link to="/" className="inline-block hover:underline">← На главную</Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
