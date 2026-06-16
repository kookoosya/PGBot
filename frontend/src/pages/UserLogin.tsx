import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";
import { getUserHomePath } from "@/lib/navigation";
import { useUserAuth } from "@/lib/userAuth";

const copy = PAGE_SECTIONS.auth;

export function UserLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { user, login } = useUserAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next");

  if (user) {
    return <Navigate to={next || getUserHomePath(user)} replace />;
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const me = await login(username, password);
      navigate(next || getUserHomePath(me));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="literary-page page-section max-w-md mx-auto">
      <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />

      <form onSubmit={submit} className="page-panel page-panel--forest literary-auth-panel literary-form-comfort space-y-4 mt-6">
        <div>
          <label htmlFor="login-username" className="event-detail-label">Логин</label>
          <Input
            id="login-username"
            placeholder="Ваш логин"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
            className="pushkin-select"
          />
        </div>
        <div>
          <label htmlFor="login-password" className="event-detail-label">Пароль</label>
          <Input
            id="login-password"
            type="password"
            placeholder="Ваш пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="pushkin-select"
          />
        </div>
        {error && <p className="text-sm text-destructive m-0">{error}</p>}
        <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={loading}>
          {loading ? "Входим…" : "Войти"}
        </button>
      </form>

      <p className="text-center text-sm mt-6 text-muted-foreground">
        Нет аккаунта?{" "}
        <Link to="/register" className="literary-link">
          Зарегистрироваться
        </Link>
        <span className="mx-2 opacity-40">·</span>
        <Link to="/admin/login" className="literary-link text-muted-foreground">
          Панель владельца
        </Link>
      </p>
    </div>
  );
}
