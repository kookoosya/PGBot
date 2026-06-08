import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const ROLES = [
  { value: "administration", label: "Администрация района" },
  { value: "social_service", label: "ЖКХ / управляющая компания" },
  { value: "moderator", label: "Модератор" },
];

export function Register() {
  const [form, setForm] = useState({
    username: "", email: "", password: "", full_name: "",
    phone: "", organization: "", position: "", role: "administration",
    verification_note: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const set = (key: string, val: string) => setForm((f) => ({ ...f, [key]: val }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.registerOfficial(form);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка регистрации");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="mx-auto max-w-lg px-6 py-16 text-center">
        <div className="pushkin-card p-10">
          <span className="text-5xl">✅</span>
          <h2 className="text-2xl font-bold mt-4">Заявка отправлена!</h2>
          <p className="text-muted-foreground mt-4">
            Ваша заявка на регистрацию передана на верификацию.
            Суперадминистратор проверит данные и активирует аккаунт.
            Вы получите доступ после одобрения.
          </p>
          <Link to="/" className="inline-block mt-6 text-primary hover:underline">
            ← На главную
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-6 py-12">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold">Регистрация службы</h2>
        <p className="text-muted-foreground mt-2">
          Для администрации, ЖКХ, управляющих компаний и соцслужб. После проверки — портал обращений жителей.
        </p>
        <p className="text-sm mt-3">
          <Link to="/register" className="text-primary hover:underline">← Все варианты регистрации</Link>
        </p>
      </div>

      <Card className="pushkin-card">
        <CardHeader>
          <CardTitle className="text-lg">Данные для верификации</CardTitle>
          <p className="text-sm text-muted-foreground">
            Все поля обязательны. Заявка проверяется вручную, чтобы посторонние не получили доступ.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">ФИО</label>
                <Input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
              </div>
              <div>
                <label className="text-sm font-medium">Телефон</label>
                <Input value={form.phone} onChange={(e) => set("phone", e.target.value)} placeholder="+7..." required />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Организация</label>
              <Input value={form.organization} onChange={(e) => set("organization", e.target.value)} placeholder="Администрация ПГО" required />
            </div>
            <div>
              <label className="text-sm font-medium">Должность</label>
              <Input value={form.position} onChange={(e) => set("position", e.target.value)} placeholder="Специалист отдела ЖКХ" required />
            </div>
            <div>
              <label className="text-sm font-medium">Роль в системе</label>
              <select
                className="w-full h-10 rounded-md border px-3 text-sm bg-background"
                value={form.role}
                onChange={(e) => set("role", e.target.value)}
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Логин</label>
                <Input value={form.username} onChange={(e) => set("username", e.target.value)} required />
              </div>
              <div>
                <label className="text-sm font-medium">Email</label>
                <Input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Пароль</label>
              <Input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} minLength={10} required />
            </div>
            <div>
              <label className="text-sm font-medium">Комментарий для проверки</label>
              <textarea
                className="w-full rounded-md border px-3 py-2 text-sm bg-background min-h-[80px]"
                value={form.verification_note}
                onChange={(e) => set("verification_note", e.target.value)}
                placeholder="Рабочий телефон, кабинет, ссылка на сайт организации..."
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Отправка..." : "Подать заявку на верификацию"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
