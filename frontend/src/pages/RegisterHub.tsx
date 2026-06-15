import { Link } from "react-router-dom";
import { LiterarySectionHead } from "@/components/literary";
import { LITERARY_VERSES, PAGE_SECTIONS } from "@/lib/literaryCopy";

const copy = PAGE_SECTIONS.register;

const options = [
  {
    to: "/signup",
    icon: "🏠",
    title: "Я житель",
    desc: "Имя, телефон и пароль — личный кабинет для объявлений, афиши и обращений.",
    badge: "2 минуты",
  },
  {
    to: "/register/organization",
    icon: "🏢",
    title: "Организация",
    desc: "Магазин, аптека, ИП — с ответственным лицом. На сайте только проверенные организации.",
    badge: "Полная форма",
  },
  {
    to: "/register/official",
    icon: "🏛",
    title: "Администрация / ЖКХ",
    desc: "Для служб посёлка. После проверки — доступ к обращениям жителей.",
    badge: "Верификация",
  },
  {
    to: "/services/register",
    icon: "💇",
    title: "Мастер услуг",
    desc: "Маникюр, стрижки, ремонт — профиль в справочнике после модерации.",
    badge: "Модерация",
  },
];

export function RegisterHub() {
  return (
    <div className="literary-page page-section max-w-3xl">
      <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />

      <div className="space-y-3 mt-6">
        {options.map((o) => (
          <Link key={o.to} to={o.to} className="literary-register-option no-underline text-inherit block">
            <span className="literary-register-option-icon" aria-hidden>{o.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="literary-title text-lg m-0">{o.title}</h2>
                <span className="literary-register-badge">{o.badge}</span>
              </div>
              <p className="text-sm text-muted-foreground mt-2 mb-0 leading-relaxed">{o.desc}</p>
            </div>
            <span className="text-xl opacity-40 shrink-0" aria-hidden>→</span>
          </Link>
        ))}
      </div>

      <p className="text-center text-sm text-muted-foreground mt-8">
        Уже есть аккаунт?{" "}
        <Link to="/cabinet/login" className="literary-link">
          Войти в кабинет
        </Link>
      </p>

      <p className="literary-page-verse literary-page-verse--inline mt-6" aria-hidden>
        {LITERARY_VERSES.register}
      </p>
    </div>
  );
}
