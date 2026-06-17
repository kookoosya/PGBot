import { useState } from "react";
import { Link } from "react-router-dom";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { api } from "@/lib/api/index";
export function RegisterOrganization() {
  const [form, setForm] = useState({
    organization_name: "",
    responsible_full_name: "",
    responsible_position: "",
    org_address: "",
    phone: "",
    email: "",
    inn: "",
    website: "",
    description: "",
    username: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.registerOrganization(form);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="literary-page page-section max-w-lg mx-auto py-12">
        <LiteraryEmptyState {...EMPTY_STATES.registerSuccess} icon="✅">
          <div className="landing-inline-actions flex flex-wrap gap-3 justify-center mt-4">
            <Link to="/cabinet/login" className="literary-btn literary-btn--primary no-underline">
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
        kicker="🏢 Организация"
        title="Регистрация организации"
        lead="Магазины, аптеки и услуги — с ответственным лицом, чтобы жители доверяли информации на портале."
        linkTo="/register"
        linkLabel="← Все варианты"
      />

      <p className="literary-page-note text-sm p-4 mb-6 mt-4">
        <strong>Зачем полная форма?</strong> На портале публикуются реальные организации посёлка.
        Нам важно знать ответственное лицо — того, кто отвечает за информацию и связь с жителями.
      </p>

      <form onSubmit={submit} className="page-panel page-panel--forest literary-auth-panel space-y-4">
        <h3 className="font-semibold">Организация</h3>
        <Input placeholder="Название (ИП Иванов / ООО ...)" value={form.organization_name} onChange={(e) => set("organization_name", e.target.value)} required />
        <Input placeholder="Адрес в посёлке" value={form.org_address} onChange={(e) => set("org_address", e.target.value)} required />
        <Input placeholder="ИНН (необязательно)" value={form.inn} onChange={(e) => set("inn", e.target.value)} />
        <Input placeholder="Сайт (необязательно)" value={form.website} onChange={(e) => set("website", e.target.value)} />
        <textarea
          className="w-full border rounded px-3 py-2 text-sm min-h-[80px]"
          placeholder="Чем занимается организация? (мин. 20 символов)"
          value={form.description}
          onChange={(e) => set("description", e.target.value)}
          required
          minLength={20}
        />

        <h3 className="font-semibold pt-2">Ответственное лицо</h3>
        <Input placeholder="ФИО полностью" value={form.responsible_full_name} onChange={(e) => set("responsible_full_name", e.target.value)} required />
        <Input placeholder="Должность (директор, управляющий...)" value={form.responsible_position} onChange={(e) => set("responsible_position", e.target.value)} required />
        <Input placeholder="Телефон" value={form.phone} onChange={(e) => set("phone", e.target.value)} required />
        <Input type="email" placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} required />

        <h3 className="font-semibold pt-2">Вход в кабинет</h3>
        <Input placeholder="Логин" value={form.username} onChange={(e) => set("username", e.target.value)} required />
        <Input type="password" placeholder="Пароль" value={form.password} onChange={(e) => set("password", e.target.value)} required minLength={10} />

        {error && <p className="text-sm text-destructive m-0">{error}</p>}
        <button type="submit" className="literary-btn literary-btn--primary w-full" disabled={loading}>
          {loading ? "Отправка…" : "Подать на проверку"}
        </button>
      </form>
    </div>
  );
}
