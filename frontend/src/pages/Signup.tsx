import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useUserAuth } from "@/lib/userAuth";

export function Signup() {
  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    username: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useUserAuth();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.registerResident(form);
      await login(form.username, form.password);
      navigate("/cabinet");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка регистрации");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="literary-page page-section max-w-md mx-auto">
      <LiterarySectionHead
        kicker="🏠 Житель"
        title="Регистрация жителя"
        lead="Простая форма — имя, контакты и пароль. Сразу откроется личный кабинет."
        linkTo="/register"
        linkLabel="← Все варианты"
      />

      <form onSubmit={submit} className="page-panel page-panel--gold literary-auth-panel space-y-4 mt-6">
        <Input
          placeholder="Как к вам обращаться?"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
          className="pushkin-select"
        />
        <Input
          placeholder="Телефон"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
          className="pushkin-select"
        />
        <Input
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
          className="pushkin-select"
        />
        <Input
          placeholder="Логин"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
          className="pushkin-select"
        />
        <Input
          type="password"
          placeholder="Пароль (от 10 символов)"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
          minLength={10}
          className="pushkin-select"
        />
        {error && <p className="text-sm text-destructive m-0">{error}</p>}
        <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={loading}>
          {loading ? "Создаём кабинет…" : "Зарегистрироваться"}
        </button>
      </form>
    </div>
  );
}
