import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { VillageGallery } from "@/components/VillageGallery";
import { BRAND } from "@/lib/branding";

const features = [
  {
    icon: "📋",
    title: "Объявления",
    desc: "Дрова, строительство, вакансии — размещение 150 ₽, поддержка проекта",
  },
  {
    icon: "💇",
    title: "Услуги мастеров",
    desc: "Маникюр, стрижки — мастера сами ведут расписание и отмечают занятость",
  },
  {
    icon: "🗺",
    title: "Карта поселка",
    desc: "Магазины, аптеки, службы — с отзывами и жалобами на обман с ценами",
  },
  {
    icon: "📝",
    title: "Обращения жителей",
    desc: "Напишите боту ВКонтакте о проблеме — мы передадим ответственным службам",
  },
  {
    icon: "🤖",
    title: "ИИ-помощник",
    desc: "Умный собеседник в духе Пушкинских Гор — бесплатно, с разумными лимитами",
  },
  {
    icon: "🏛",
    title: "Контроль решений",
    desc: "Администрация и службы отслеживают статус каждого обращения",
  },
  {
    icon: "🔒",
    title: "Верификация служб",
    desc: "Только проверенные сотрудники получают доступ к панели управления",
  },
];

export function Landing() {
  return (
    <div>
      <section className="pushkin-gradient relative overflow-hidden px-6 py-24 text-white">
        <div className="absolute inset-0 opacity-10 feather-pattern" />
        <div className="relative mx-auto max-w-4xl text-center">
          <p className="mb-4 text-amber-300 font-serif italic text-lg">
            «Любви, надежды, тихой славы...»
          </p>
          <h2 className="text-4xl font-bold md:text-6xl leading-tight">
            {BRAND.name}
          </h2>
          <p className="mt-3 text-2xl md:text-3xl text-amber-300 font-serif">
            {BRAND.tagline}
          </p>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-white/80">
            Сайт для жителей посёлка: объявления, мастера, карта магазинов и служб,
            обращения в администрацию. Земля Пушкина — наш общий дом.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Link to="/map">
              <Button size="lg" className="bg-amber-500 text-green-950 hover:bg-amber-400 font-semibold px-8">
                🗺 Карта поселка
              </Button>
            </Link>
            <Link to="/ai">
              <Button size="lg" variant="outline" className="border-white/30 text-white hover:bg-white/10 px-8">
                🤖 ИИ-помощник
              </Button>
            </Link>
            <a
              href="https://vk.com"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="lg" variant="outline" className="border-white/30 text-white hover:bg-white/10 px-8">
                📱 Бот ВКонтакте
              </Button>
            </a>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20">
        <h3 className="text-center text-3xl font-bold mb-12">Как это работает</h3>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {features.map((f) => (
            <div key={f.title} className="pushkin-card p-6 text-center transition hover:shadow-xl">
              <div className="text-4xl mb-4">{f.icon}</div>
              <h4 className="text-lg font-semibold mb-2">{f.title}</h4>
              <p className="text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-secondary/50 py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h3 className="text-3xl font-bold mb-6">Для администрации и служб</h3>
          <p className="text-muted-foreground mb-8">
            Зарегистрируйтесь на сайте, укажите организацию и должность.
            После верификации суперадминистратором вы получите доступ к панели управления обращениями.
          </p>
          <Link to="/register">
            <Button size="lg" className="px-8">
              🏛 Зарегистрировать службу
            </Button>
          </Link>
        </div>
      </section>

      <VillageGallery />

      <section className="mx-auto max-w-4xl px-6 py-12 text-center">
        <div className="pushkin-card p-10">
          <span className="text-5xl">🪶</span>
          <blockquote className="mt-6 text-xl font-serif italic text-foreground/80">
            «Я памятник себе воздвиг нерукотворный,<br />
            К ногам его железный век не наступит...»
          </blockquote>
          <p className="mt-4 text-sm text-muted-foreground">
            А мы вместе возводим порядок и уют в нашем поселке
          </p>
        </div>
      </section>
    </div>
  );
}
