import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { api } from "@/lib/api/index";
const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function ServiceRegister() {
  const [types, setTypes] = useState<{ value: string; label: string }[]>([]);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    full_name: "", phone: "", email: "", username: "", password: "",
    bio: "", address: "",
    service_type: "manicure", service_name: "", service_duration: 60, service_price: "",
    schedule: DAYS.map((_, i) => ({
      day_of_week: i, start_time: i < 5 ? "09:00" : i === 5 ? "10:00" : "09:00",
      end_time: i < 5 ? "18:00" : i === 5 ? "16:00" : "18:00",
      is_working: i < 6,
    })),
  });

  useEffect(() => { api.getServiceTypes().then(setTypes).catch(console.error); }, []);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.registerProvider({
        full_name: form.full_name,
        phone: form.phone,
        email: form.email || undefined,
        username: form.username,
        password: form.password,
        bio: form.bio,
        address: form.address,
        services: [{
          service_type: form.service_type,
          name: form.service_name,
          duration_minutes: form.service_duration,
          price: form.service_price ? +form.service_price : undefined,
        }],
        schedule: form.schedule.filter((s) => s.is_working).map((s) => ({
          day_of_week: s.day_of_week,
          start_time: s.start_time,
          end_time: s.end_time,
          is_working: true,
        })),
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  };

  if (success) {
    return (
      <div className="literary-page page-section max-w-lg mx-auto py-12">
        <LiteraryEmptyState {...EMPTY_STATES.registerSuccess} icon="✅">
          <div className="landing-inline-actions flex flex-wrap gap-3 justify-center mt-4">
            <Link to="/cabinet/login?next=/services/cabinet" className="literary-btn literary-btn--primary no-underline">
              Войти после одобрения →
            </Link>
            <Link to="/services" className="literary-btn literary-btn--ghost no-underline">К услугам</Link>
          </div>
        </LiteraryEmptyState>
      </div>
    );
  }

  return (
    <div className="literary-page page-section max-w-xl mx-auto">
      <LiterarySectionHead
        kicker="💇 Мастер"
        title="Регистрация мастера"
        lead="Маникюр, стрижки, брови и другие услуги — профиль в справочнике после модерации."
        linkTo="/register"
        linkLabel="← Все варианты"
      />

      <form onSubmit={submit} className="page-panel page-panel--gold literary-auth-panel space-y-4 mt-6">
            <Input placeholder="ФИО" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
            <Input placeholder="Телефон" value={form.phone} onChange={(e) => set("phone", e.target.value)} required />
            <Input placeholder="Адрес приёма" value={form.address} onChange={(e) => set("address", e.target.value)} />
            <textarea className="w-full border rounded px-3 py-2 text-sm min-h-[60px]" placeholder="О себе" value={form.bio} onChange={(e) => set("bio", e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              <Input placeholder="Логин" value={form.username} onChange={(e) => set("username", e.target.value)} required />
              <Input type="password" placeholder="Пароль" value={form.password} onChange={(e) => set("password", e.target.value)} required />
            </div>
            <Input type="email" placeholder="Email" value={form.email} onChange={(e) => set("email", e.target.value)} />
            <hr />
            <p className="font-medium text-sm">Услуга</p>
            <select className="w-full border rounded px-3 py-2 text-sm" value={form.service_type} onChange={(e) => set("service_type", e.target.value)}>
              {types.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
            <Input placeholder="Название (напр. Классический маникюр)" value={form.service_name} onChange={(e) => set("service_name", e.target.value)} required />
            <div className="grid grid-cols-2 gap-2">
              <Input type="number" placeholder="Минут" value={form.service_duration} onChange={(e) => set("service_duration", e.target.value)} />
              <Input type="number" placeholder="Цена ₽" value={form.service_price} onChange={(e) => set("service_price", e.target.value)} />
            </div>
            <hr />
            <p className="font-medium text-sm">Расписание</p>
            {form.schedule.map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <label className="w-8 flex items-center gap-1">
                  <input type="checkbox" checked={s.is_working} onChange={(e) => {
                    const sch = [...form.schedule];
                    sch[i] = { ...sch[i], is_working: e.target.checked };
                    setForm({ ...form, schedule: sch });
                  }} />
                  {DAYS[i]}
                </label>
                {s.is_working && (
                  <>
                    <input className="border rounded px-2 py-1 w-20" value={s.start_time} onChange={(e) => {
                      const sch = [...form.schedule]; sch[i].start_time = e.target.value; setForm({ ...form, schedule: sch });
                    }} />
                    <span>—</span>
                    <input className="border rounded px-2 py-1 w-20" value={s.end_time} onChange={(e) => {
                      const sch = [...form.schedule]; sch[i].end_time = e.target.value; setForm({ ...form, schedule: sch });
                    }} />
                  </>
                )}
              </div>
            ))}
            {error && <p className="text-sm text-destructive m-0">{error}</p>}
            <button type="submit" className="literary-btn literary-btn--primary w-full">Подать заявку</button>
      </form>
    </div>
  );
}
