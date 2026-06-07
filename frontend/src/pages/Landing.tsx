import { Link } from "react-router-dom";
import { QuickNav } from "@/components/QuickNav";
import { VillageGallery } from "@/components/VillageGallery";
import { BRAND } from "@/lib/branding";

const features = [
  { icon: "📋", title: "Объявления", desc: "Дрова, строительство, вакансии от жителей", to: "/classifieds" },
  { icon: "💇", title: "Услуги мастеров", desc: "Маникюр, стрижки — запись по расписанию", to: "/services" },
  { icon: "🗺", title: "Карта посёлка", desc: "Магазины, аптеки, отзывы и жалобы", to: "/map" },
  { icon: "📝", title: "Обращения", desc: "Сообщите о проблеме через бот ВКонтакте", to: "/" },
  { icon: "🤖", title: "ИИ-помощник", desc: "Ответы о посёлке и помощь с текстом", to: "/ai" },
  { icon: "🏛", title: "Для служб", desc: "Регистрация и верификация сотрудников", to: "/register" },
];

export function Landing() {
  return (
    <div>
      <section className="pushkin-gradient hero-section">
        <div className="absolute inset-0 opacity-10 feather-pattern" />
        <div className="hero-content">
          <p className="hero-quote">«Любви, надежды, тихой славы...»</p>
          <h2 className="hero-title">{BRAND.name}</h2>
          <p className="hero-tagline">{BRAND.tagline}</p>
          <p className="hero-desc">
            Всё для жителей в одном месте: объявления, мастера, карта, обращения.
            {BRAND.district}.
          </p>
          <div className="hero-actions">
            <Link to="/map" className="btn-hero-primary">🗺 Карта посёлка</Link>
            <Link to="/classifieds" className="btn-hero-secondary">📋 Объявления</Link>
            <Link to="/ai" className="btn-hero-secondary">🤖 ИИ-помощник</Link>
          </div>
        </div>
      </section>

      <section className="page-section -mt-2">
        <h3 className="section-title">Разделы портала</h3>
        <QuickNav />
      </section>

      <section className="section-alt">
        <div className="page-section">
          <h3 className="section-title">Что есть на сайте</h3>
          <div className="feature-grid">
            {features.map((f) => (
              <Link key={f.title} to={f.to} className="feature-card no-underline text-inherit">
                <div className="feature-icon">{f.icon}</div>
                <h4 className="feature-title">{f.title}</h4>
                <p className="feature-desc">{f.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="page-section">
        <div className="pushkin-card p-8 md:p-10 text-center max-w-2xl mx-auto">
          <span className="text-5xl">🪶</span>
          <blockquote className="mt-6 text-xl font-serif italic text-foreground/80 leading-relaxed">
            «Я памятник себе воздвиг нерукотворный,<br />
            К ногам его железный век не наступит...»
          </blockquote>
          <p className="mt-4 text-sm text-muted-foreground">
            А мы вместе возводим порядок и уют в нашем посёлке
          </p>
        </div>
      </section>

      <VillageGallery />
    </div>
  );
}
