import { Link } from "react-router-dom";
import { BRAND } from "@/lib/branding";

const options = [
  {
    to: "/signup",
    icon: "🏠",
    title: "Я житель",
    desc: "Простая регистрация — имя, телефон и пароль. Личный кабинет для объявлений и отзывов.",
    badge: "2 минуты",
  },
  {
    to: "/register/organization",
    icon: "🏢",
    title: "Организация",
    desc: "Магазин, аптека, ИП — полная регистрация с ответственным лицом. Проверяем, чтобы на сайте были только настоящие организации.",
    badge: "Полная форма",
  },
  {
    to: "/register/official",
    icon: "🏛",
    title: "Служба / администрация",
    desc: "Для сотрудников администрации и соцслужб. Доступ после ручной проверки.",
    badge: "Верификация",
  },
  {
    to: "/services/register",
    icon: "💇",
    title: "Мастер услуг",
    desc: "Маникюр, стрижки, ремонт — профиль в каталоге после модерации.",
    badge: "Модерация",
  },
];

export function RegisterHub() {
  return (
    <div className="page-section max-w-3xl">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold">Регистрация на портале</h1>
        <p className="text-muted-foreground mt-3 max-w-xl mx-auto">
          {BRAND.name} — для жителей, бизнеса и служб. Выберите подходящий вариант.
        </p>
      </div>

      <div className="space-y-4">
        {options.map((o) => (
          <Link key={o.to} to={o.to} className="register-option-card no-underline text-inherit">
            <span className="text-4xl">{o.icon}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-xl font-bold m-0">{o.title}</h2>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-900">
                  {o.badge}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-2 mb-0">{o.desc}</p>
            </div>
            <span className="text-2xl opacity-50">→</span>
          </Link>
        ))}
      </div>

      <p className="text-center text-sm text-muted-foreground mt-8">
        Уже есть аккаунт? <Link to="/cabinet/login" className="text-primary hover:underline">Войти в кабинет</Link>
      </p>
    </div>
  );
}
