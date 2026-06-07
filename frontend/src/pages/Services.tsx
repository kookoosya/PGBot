import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClassifiedMarketingCharts } from "@/components/ClassifiedMarketingCharts";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { api, ClassifiedMarketingStats, ServiceProvider, TimeSlot } from "@/lib/api";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

const STATUS: Record<string, { label: string; color: string }> = {
  free: { label: "🟢 Свободен", color: "text-green-700" },
  busy: { label: "🔴 Занят", color: "text-red-600" },
  off: { label: "⚫ Выходной", color: "text-gray-500" },
};

export function Services() {
  const [providers, setProviders] = useState<ServiceProvider[]>([]);
  const [types, setTypes] = useState<{ value: string; label: string }[]>([]);
  const [filter, setFilter] = useState("");
  const [booking, setBooking] = useState<ServiceProvider | null>(null);
  const [serviceId, setServiceId] = useState(0);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [workingHours, setWorkingHours] = useState("");
  const [form, setForm] = useState({ client_name: "", client_phone: "", notes: "" });
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [marketing, setMarketing] = useState<ClassifiedMarketingStats | null>(null);

  useEffect(() => {
    api.getServiceTypes().then(setTypes).catch(console.error);
    api.getClassifiedMarketingStats().then(setMarketing).catch(console.error);
    loadProviders();
  }, [filter]);

  const loadProviders = () => {
    const params = filter ? { service_type: filter } : undefined;
    api.getProviders(params).then(setProviders).catch(console.error);
  };

  const openBooking = (p: ServiceProvider) => {
    setBooking(p);
    setServiceId(p.services[0]?.id || 0);
    setSelectedSlot("");
    setMsg("");
    setForm({ client_name: "", client_phone: "", notes: "" });
  };

  const loadSlots = async (sid: number, d: string) => {
    if (!booking || !sid) return;
    const res = await api.getSlots(booking.id, sid, d);
    setSlots(res.slots);
    setWorkingHours(res.working_hours || "");
  };

  useEffect(() => {
    if (booking && serviceId && date) loadSlots(serviceId, date);
  }, [booking, serviceId, date]);

  const submitBooking = async () => {
    if (!booking || !selectedSlot) return;
    setLoading(true);
    try {
      await api.bookAppointment(booking.id, {
        service_id: serviceId,
        appointment_date: date,
        start_time: selectedSlot,
        ...form,
      });
      setMsg("✅ Запись подтверждена! Уведомление отправлено — мастер свяжется с вами.");
      loadProviders();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Ошибка записи");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section max-w-5xl">
      <PageHeader
        icon="💇"
        title="Услуги и мастера"
        subtitle={PUSHKIN_QUOTES.services}
      >
        <Link to="/services/register" className="btn-hero-secondary text-sm">Стать мастером</Link>
        <Link to="/services/cabinet" className="btn-hero-secondary text-sm">Кабинет мастера</Link>
      </PageHeader>

      {marketing && <ClassifiedMarketingCharts stats={marketing} />}

      <div className="filter-bar">
        <button type="button" className={`filter-chip ${!filter ? "filter-chip-active" : ""}`} onClick={() => setFilter("")}>Все</button>
        {types.map((t) => (
          <button key={t.value} type="button" className={`filter-chip ${filter === t.value ? "filter-chip-active" : ""}`} onClick={() => setFilter(t.value)}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {providers.map((p) => (
          <div
            key={p.id}
            className="pushkin-card-hover p-5 cursor-pointer"
            role="button"
            tabIndex={0}
            onClick={() => p.status_today !== "off" && openBooking(p)}
            onKeyDown={(e) => e.key === "Enter" && p.status_today !== "off" && openBooking(p)}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-bold text-lg">{p.full_name}</h3>
                <p className={`text-sm font-medium ${STATUS[p.status_today]?.color}`}>
                  {STATUS[p.status_today]?.label}
                  {p.next_free_slot && ` · ближайшее: ${p.next_free_slot}`}
                </p>
              </div>
              {p.avg_rating > 0 && <span className="text-sm">⭐ {p.avg_rating}</span>}
            </div>
            {p.bio && <p className="text-sm text-muted-foreground mt-2">{p.bio}</p>}
            {p.address && <p className="text-xs mt-1">📍 {p.address}</p>}
            <div className="mt-3 flex flex-wrap gap-2">
              {p.services.map((s) => (
                <span key={s.id} className="text-xs bg-secondary rounded-full px-2 py-1">
                  {s.name} {s.price ? `— ${s.price} ₽` : ""}
                </span>
              ))}
            </div>
            <Button
              className="w-full mt-4"
              size="sm"
              onClick={(e) => { e.stopPropagation(); openBooking(p); }}
              disabled={p.status_today === "off"}
            >
              {p.status_today === "off" ? "Выходной" : "Записаться →"}
            </Button>
          </div>
        ))}
        {providers.length === 0 && (
          <div className="col-span-2 text-center py-12 pushkin-card p-8">
            <span className="text-4xl">💇</span>
            <p className="mt-4 text-muted-foreground">
              Пока нет зарегистрированных мастеров.
            </p>
            <p className="text-sm mt-2">
              Маникюр, стрижки, брови — <Link to="/services/register" className="text-primary underline">зарегистрируйтесь</Link> и ведите своё расписание сами.
            </p>
          </div>
        )}
      </div>

      {booking && (
        <div className="modal-overlay" onClick={() => setBooking(null)}>
          <div className="pushkin-card bg-card p-6 max-w-md w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-bold text-lg">Запись к {booking.full_name}</h3>
            {msg && <p className="text-sm mt-2 text-green-700">{msg}</p>}
            {!msg && (
              <div className="mt-4 space-y-3">
                <select className="w-full border rounded px-3 py-2 text-sm" value={serviceId} onChange={(e) => setServiceId(+e.target.value)}>
                  {booking.services.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} — {s.duration_minutes} мин{s.price ? `, ${s.price} ₽` : ""}</option>
                  ))}
                </select>
                <input type="date" className="w-full border rounded px-3 py-2 text-sm" value={date} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setDate(e.target.value)} />
                {workingHours && <p className="text-xs text-muted-foreground">🕐 Работает: {workingHours}</p>}
                <div className="grid grid-cols-4 gap-2">
                  {slots.map((s) => (
                    <button
                      key={s.time}
                      disabled={!s.available}
                      className={`text-sm py-2 rounded border ${selectedSlot === s.time ? "bg-primary text-primary-foreground" : s.available ? "hover:bg-muted" : "opacity-40 line-through"}`}
                      onClick={() => s.available && setSelectedSlot(s.time)}
                    >
                      {s.time}
                    </button>
                  ))}
                </div>
                {slots.length === 0 && <p className="text-sm text-muted-foreground">Нет слотов на этот день</p>}
                <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Ваше имя" value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })} />
                <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Телефон" value={form.client_phone} onChange={(e) => setForm({ ...form, client_phone: e.target.value })} />
                <Button className="w-full" disabled={!selectedSlot || !form.client_name || !form.client_phone || loading} onClick={submitBooking}>
                  {loading ? "Запись..." : "Подтвердить запись"}
                </Button>
              </div>
            )}
            <Button variant="outline" className="w-full mt-3" onClick={() => setBooking(null)}>Закрыть</Button>
          </div>
        </div>
      )}
    </div>
  );
}
