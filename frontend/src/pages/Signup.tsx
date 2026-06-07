import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
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
    <div className="page-section max-w-md mx-auto">
      <h1 className="text-2xl font-bold text-center mb-2">Регистрация жителя</h1>
      <p className="text-center text-sm text-muted-foreground mb-8">
        Простая форма — без лишних полей. Сразу получите личный кабинет.
      </p>

      <form onSubmit={submit} className="pushkin-card p-6 space-y-4">
        <Input
          placeholder="Как к вам обращаться?"
          value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          required
        />
        <Input
          placeholder="Телефон"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
        />
        <Input
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <Input
          placeholder="Логин"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <Input
          type="password"
          placeholder="Пароль (от 10 символов)"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
          minLength={10}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Создаём кабинет..." : "Зарегистрироваться"}
        </Button>
      </form>

      <p className="text-center text-sm mt-6 text-muted-foreground">
        <Link to="/register" className="hover:underline">← Все варианты регистрации</Link>
      </p>
    </div>
  );
}
