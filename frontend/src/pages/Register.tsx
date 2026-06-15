import { useState } from "react";
import { Link } from "react-router-dom";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { EMPTY_STATES, LITERARY_VERSES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import { api } from "@/lib/api";

const ROLES = [
  { value: "administration", label: "Администрация района" },
  { value: "social_service", label: "ЖКХ / управляющая компания" },
  { value: "moderator", label: "Модератор" },
];

const copy = PAGE_SECTIONS.registerOfficial;

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
      <div className="literary-page page-section max-w-lg mx-auto py-12">
        <LiteraryEmptyState {...EMPTY_STATES.registerOfficialSuccess}>
          <div className="landing-inline-actions flex flex-wrap gap-3 justify-center mt-4">
            <Link to="/cabinet/login?next=/official" className="literary-btn literary-btn--primary no-underline">
              Войти после одобрения →
            </Link>
            <Link to="/" className="literary-btn literary-btn--ghost no-underline">На главную</Link>
          </div>
        </LiteraryEmptyState>
      </div>
    );
  }

  return (
    <div className="literary-page page-section max-w-xl mx-auto">
      <LiterarySectionHead
        kicker={copy.kicker}
        title={copy.title}
        lead={copy.lead}
        linkTo="/register"
        linkLabel="← Все варианты"
      />

      <p className="literary-page-note text-sm p-4 mb-6 mt-4">
        <strong>Зачем верификация?</strong> Портал обращений — для служб посёлка.
        Заявка проверяется вручную, чтобы посторонние не получили доступ к заявкам жителей.
      </p>

      <form onSubmit={handleSubmit} className="page-panel page-panel--forest literary-auth-panel space-y-4">
        <h3 className="font-semibold m-0">Сотрудник</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <Input
            placeholder="ФИО полностью"
            value={form.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            required
          />
          <Input
            placeholder="Телефон (+7...)"
            value={form.phone}
            onChange={(e) => set("phone", e.target.value)}
            required
          />
        </div>
        <Input
          placeholder="Организация (Администрация ПГО)"
          value={form.organization}
          onChange={(e) => set("organization", e.target.value)}
          required
        />
        <Input
          placeholder="Должность (специалист отдела ЖКХ)"
          value={form.position}
          onChange={(e) => set("position", e.target.value)}
          required
        />
        <div>
          <label className="text-sm font-medium text-muted-foreground mb-1.5 block">Роль в системе</label>
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

        <h3 className="font-semibold pt-2 m-0">Учётная запись</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <Input
            placeholder="Логин"
            value={form.username}
            onChange={(e) => set("username", e.target.value)}
            required
          />
          <Input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            required
          />
        </div>
        <Input
          type="password"
          placeholder="Пароль (не менее 10 символов)"
          value={form.password}
          onChange={(e) => set("password", e.target.value)}
          minLength={10}
          required
        />
        <div>
          <label className="text-sm font-medium text-muted-foreground mb-1.5 block">Комментарий для проверки</label>
          <textarea
            className="w-full rounded-md border px-3 py-2 text-sm bg-background min-h-[80px]"
            value={form.verification_note}
            onChange={(e) => set("verification_note", e.target.value)}
            placeholder="Рабочий телефон, кабинет, ссылка на сайт организации…"
          />
        </div>

        {error && <p className="text-sm text-destructive m-0">{error}</p>}
        <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={loading}>
          {loading ? "Отправка…" : "Подать заявку на верификацию"}
        </button>
      </form>

      <p className="literary-page-verse literary-page-verse--inline mt-8" aria-hidden>
        {LITERARY_VERSES.register}
      </p>
    </div>
  );
}
