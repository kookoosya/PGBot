import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useUserAuth } from "@/lib/userAuth";

export function UserLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { user, login } = useUserAuth();
  const navigate = useNavigate();

  if (user) return <Navigate to="/cabinet" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      navigate("/cabinet");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section max-w-md mx-auto">
      <h1 className="text-2xl font-bold text-center mb-2">Вход в личный кабинет</h1>
      <p className="text-center text-sm text-muted-foreground mb-8">
        Для жителей и организаций. Владелец сайта входит через{" "}
        <Link to="/admin/login" className="text-primary hover:underline">отдельную панель</Link>.
      </p>

      <form onSubmit={submit} className="pushkin-card p-6 space-y-4">
        <Input
          placeholder="Логин"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          autoComplete="username"
        />
        <Input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Входим..." : "Войти"}
        </Button>
      </form>

      <p className="text-center text-sm mt-6 text-muted-foreground">
        Нет аккаунта? <Link to="/register" className="text-primary hover:underline">Зарегистрироваться</Link>
      </p>
    </div>
  );
}
