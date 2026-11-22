import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { VkBotLink } from "@/components/VkBotLink";
import {
  estimateMounting, formatRubles, REMOVAL_INSTALLATION, ROSSVIK_VIDEOS,
  STUDDING, TIRE_SERVICE, TIRE_SIZE_PRICES, TUBE_REPAIR, TUBELESS_REPAIR,
  type ServicePrice,
} from "@/lib/tireService";
import "@/styles/tire-service.css";

type PriceCategory = "mount" | "repair" | "tube" | "studding";
const CATEGORIES: { id: PriceCategory; label: string }[] = [
  { id: "mount", label: "Перебортовка" }, { id: "repair", label: "Ремонт шин" },
  { id: "tube", label: "Ремонт камер" }, { id: "studding", label: "Дошиповка" },
];
const SECTIONS = [
  { id: "tire-top", label: "Главная" }, { id: "tire-services", label: "Услуги" },
  { id: "tire-prices", label: "Прайс" }, { id: "tire-methods", label: "Как работаем" },
  { id: "village", label: "Пушкинские Горы" }, { id: "tire-location", label: "Контакты" },
];
const VILLAGE_LINKS = [
  { to: "/map", label: "Карта посёлка", text: "Места, организации и маршруты" },
  { to: "/events", label: "Афиша", text: "События и мероприятия" },
  { to: "/classifieds", label: "Объявления", text: "Предложения жителей" },
  { to: "/jobs", label: "Работа", text: "Вакансии и резюме" },
  { to: "/services", label: "Местные услуги", text: "Специалисты и организации" },
  { to: "/complaints", label: "Обращения", text: "Сообщить о проблеме" },
];
const SERVICES: { category: PriceCategory; title: string; text: string }[] = [
  { category: "mount", title: "Перебортовка и балансировка", text: "R12–R20, микроавтобусы, Газель и УАЗ. Разборка, сборка и балансировка колеса." },
  { category: "repair", title: "Ремонт бескамерных шин", text: "Проколы, порезы, проверка герметичности и вулканизация. Способ ремонта зависит от повреждения." },
  { category: "tube", title: "Ремонт камер", text: "Легковые и грузовые камеры. Ремонт проколов, порезов и вклейка вентиля." },
  { category: "studding", title: "Дошиповка", text: "Удаление старых шипов и установка ремонтных. Цена за каждый шип, материал включён." },
];
function PriceRows({ items }: { items: readonly ServicePrice[] }) {
  return <dl className="tire-service-rows">{items.map((item) => (
    <div className="tire-service-row" key={item.name}><dt>{item.name}</dt><dd>{item.price}</dd></div>
  ))}</dl>;
}
export function TireServiceLanding() {
  const [category, setCategory] = useState<PriceCategory>("mount");
  const [size, setSize] = useState("R16");
  const [count, setCount] = useState(4);
  const [activeSection, setActiveSection] = useState("tire-top");
  const menu = useRef<HTMLDetailsElement>(null);
  const header = useRef<HTMLElement>(null);
  const selected = TIRE_SIZE_PRICES.find((item) => item.size === size)!;
  const estimate = estimateMounting(size, count);
  useEffect(() => {
    const sections = SECTIONS.map(({ id }) => document.getElementById(id)).reverse();
    let frame = 0;
    function updateSection() {
      frame = 0;
      const edge = (header.current?.offsetHeight ?? 0) + 24;
      const atBottom = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2;
      const section = atBottom ? sections[0] : sections.find((node) => node && node.getBoundingClientRect().top <= edge);
      setActiveSection(section?.id ?? SECTIONS[0].id);
    }
    function onScroll() {
      if (!frame) frame = window.requestAnimationFrame(updateSection);
    }
    updateSection();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      window.cancelAnimationFrame(frame);
    };
  }, []);
  function closeMenu() { if (menu.current) menu.current.open = false; }
  return (
    <div className="tire-landing">
      <a className="tire-skip" href="#tire-top">К содержимому</a>
      <header className="tire-header" ref={header}>
        <a className="tire-brand" href="#tire-top" aria-label="PG, Пушкинские Горы, главная">PG<span>Пушкинские<br />Горы</span></a>
        <nav className="tire-desktop-nav" aria-label="Разделы главной">
          {SECTIONS.map((section) => <a key={section.id} href={`#${section.id}`} aria-current={activeSection === section.id ? "location" : undefined}>{section.label}</a>)}
          <Link to="/map">Карта</Link>
        </nav>
        <Link className="tire-account" to="/cabinet">Кабинет</Link>
        <details className="tire-mobile-menu" ref={menu} onKeyDown={(event) => {
          if (event.key === "Escape" && event.currentTarget.open) {
            closeMenu();
            event.currentTarget.querySelector("summary")?.focus();
          }
        }}><summary>Меню</summary><nav aria-label="Мобильная навигация">
          {SECTIONS.map((section) => <a key={section.id} href={`#${section.id}`} onClick={closeMenu} aria-current={activeSection === section.id ? "location" : undefined}>{section.label}</a>)}
          <Link to="/map">Карта</Link><Link to="/cabinet">Кабинет</Link>
        </nav></details>
      </header>
      <main id="main-content">
      <section className="tire-hero" id="tire-top" tabIndex={-1} aria-labelledby="tire-hero-title">
        <div className="tire-hero-copy">
          <p className="tire-address">Пушкинские Горы, Аэродромная, 23</p>
          <h1 id="tire-hero-title">Шиномонтаж <span>на Аэродромной</span></h1>
          <p className="tire-hero-description">Перебортовка, балансировка и ремонт шин.</p>
          <div className="tire-actions"><a className="tire-button tire-button-primary" href="#tire-prices">Смотреть цены</a><a className="tire-button tire-button-outline" href={TIRE_SERVICE.phoneHref}>Позвонить</a></div>
          <a className="tire-route-link" href={TIRE_SERVICE.yandexRouteUrl} target="_blank" rel="noopener noreferrer">Построить маршрут <span aria-hidden="true">↗</span></a>
          <p className="tire-hero-note">Грузики включены в перебортовку.<br />Снятие и установка колёс оплачиваются отдельно.</p>
        </div>
        <figure className="tire-hero-photo"><img src="/images/pg/tire-1280.webp" srcSet="/images/pg/tire-640.webp 640w, /images/pg/tire-1280.webp 960w" sizes="(max-width: 767px) 100vw, 48vw" width="960" height="1280" alt="Крупный план протектора автомобильной шины" /></figure>
      </section>
      <section id="tire-services" className="tire-section tire-services">
        <div className="tire-section-heading"><h2>Услуги <em>шиномонтажа</em></h2></div>
        <div className="tire-services-list">{SERVICES.map((service) => <a key={service.category} href="#tire-prices" onClick={() => setCategory(service.category)}><h3>{service.title}</h3><p>{service.text}</p></a>)}</div>
      </section>
      <section id="tire-prices" className="tire-section tire-pricing">
        <div className="tire-section-heading"><h2>Стоимость работ</h2><p>Прайс от {TIRE_SERVICE.priceRevision}. Комплектные цены приведены отдельно.</p></div>
        <div className="tire-price-panel">
          <div className="tire-price-categories" role="group" aria-label="Категория услуг">{CATEGORIES.map((item) => <button key={item.id} type="button" aria-pressed={category === item.id} onClick={() => setCategory(item.id)}>{item.label}</button>)}</div>
          <div className="tire-price-content">{category === "mount" ? <>
            <div className="tire-calculator-fields">
              <label>Размер или транспорт<select value={size} onChange={(event) => { const value = event.target.value; setSize(value); setCount(TIRE_SIZE_PRICES.find((item) => item.size === value)!.setCount); }}>
                <optgroup label="Легковые автомобили">{TIRE_SIZE_PRICES.slice(0, 9).map((item) => <option key={item.size}>{item.size}</option>)}</optgroup>
                <optgroup label="Другой транспорт">{TIRE_SIZE_PRICES.slice(9).map((item) => <option key={item.size}>{item.size}</option>)}</optgroup>
              </select></label>
              <label>Количество колёс<select value={count} onChange={(event) => setCount(Number(event.target.value))}>{[1, 2, 3, 4, 5, 6].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
            </div>
            <div className="tire-calculation" role="status" aria-live="polite" aria-atomic="true"><p>{selected.size}, {count} {count === 1 ? "колесо" : count < 5 ? "колеса" : "колёс"}</p><strong>{formatRubles(estimate.amount)}</strong><p>{estimate.usesSetPrice ? `Опубликованная цена комплекта из ${selected.setCount} колёс` : `${formatRubles(selected.wheel)} × ${count}`}</p></div>
            <p className="tire-price-note">Снятие и установка оплачиваются отдельно. Грузики включены в перебортовку.</p>
            <details className="tire-price-breakdown"><summary>Из чего складывается цена</summary><PriceRows items={[
              { name: "Разборка одного колеса", price: formatRubles(selected.dismount) }, { name: "Сборка одного колеса", price: formatRubles(selected.mount) },
              { name: "Балансировка одного колеса", price: formatRubles(selected.balance) }, { name: "Одно колесо полностью", price: formatRubles(selected.wheel) },
              { name: `Комплект из ${selected.setCount} колёс`, price: formatRubles(selected.set) },
            ]} /></details>
            <details className="tire-price-breakdown"><summary>Весь прайс на перебортовку</summary><div className="tire-table-scroll" tabIndex={0} role="region" aria-label="Таблица цен на перебортовку"><table><caption>Разборка, сборка и балансировка. Цены в рублях.</caption><thead><tr><th scope="col">Размер</th><th scope="col">Разборка</th><th scope="col">Сборка</th><th scope="col">Баланс.</th><th scope="col">Колесо</th><th scope="col">Комплект</th></tr></thead><tbody>{TIRE_SIZE_PRICES.map((item) => <tr key={item.size}><th scope="row">{item.size}</th><td>{item.dismount}</td><td>{item.mount}</td><td>{item.balance}</td><td>{item.wheel}</td><td>{item.set} ({item.setCount} шт.)</td></tr>)}</tbody></table></div></details>
            <div className="tire-additional"><h3>Снятие и установка</h3><PriceRows items={REMOVAL_INSTALLATION} /><p className="tire-price-note">Единицу тарификации уточните по телефону. Эти работы не включены в расчёт выше.</p></div>
          </> : <><h3>{CATEGORIES.find((item) => item.id === category)!.label}</h3><PriceRows items={category === "repair" ? TUBELESS_REPAIR : category === "tube" ? TUBE_REPAIR : STUDDING} />{category === "repair" && <p className="tire-price-note">Цена зависит от характера повреждения, размера шины и ремонтного материала. Точную стоимость определяют после осмотра.</p>}</>}</div>
          <a className="tire-price-contact" href={TIRE_SERVICE.phoneHref}>Уточнить стоимость по телефону {TIRE_SERVICE.phoneDisplay}</a>
        </div>
      </section>
      <section id="tire-methods" className="tire-section tire-methods">
        <div className="tire-section-heading"><h2>Материалы<br /><em>и ремонт</em></h2><p>В мастерской используются материалы ROSSVIK. Способ ремонта выбирают после осмотра шины.</p></div>
        <div className="tire-method-layout"><div className="tire-method-intro"><p>Прокол, порез и потеря герметичности требуют разных решений. Размер повреждения и состояние шины важнее выбора услуги по названию.</p><a className="tire-text-link" href={TIRE_SERVICE.phoneHref}>Обсудить повреждение</a></div><div className="tire-method-list">{ROSSVIK_VIDEOS.map((video) => <details key={video.url}><summary>{video.service}</summary><p>{video.title}</p><a href={video.url} target="_blank" rel="noopener noreferrer">Смотреть материал {video.source} <span aria-hidden="true">↗</span></a></details>)}</div></div>
        <p className="tire-source-note">По ссылкам открываются учебные видео производителя.</p>
      </section>
      <section id="village" className="tire-village">
        <figure className="tire-village-photo"><img src="/images/pg/sorot-1280.webp" srcSet="/images/pg/sorot-640.webp 640w, /images/pg/sorot-1280.webp 960w" sizes="100vw" width="960" height="640" loading="lazy" decoding="async" alt="Разлив Сороти у усадьбы Михайловское весной" /><figcaption>Михайловское. Разлив Сороти.</figcaption></figure>
        <div className="tire-section tire-village-content"><div className="tire-section-heading"><h2>Пушкинские Горы</h2><p>Независимый портал для жителей и гостей посёлка.</p></div>
          <div className="tire-village-directory">{VILLAGE_LINKS.map((item) => <Link to={item.to} key={item.to}><h3>{item.label}</h3><p>{item.text}</p></Link>)}</div>
          <div className="tire-village-live"><TodayInVillage /><UpcomingEvents variant="landing" /></div>
          <div className="tire-more-links">
            <Link to="/wishes">Пожелания для посёлка</Link><Link to="/ai">Помощник PG</Link><Link to="/cabinet">Личный кабинет</Link>
            <VkBotLink className="tire-vk-link" />
          </div>
        </div>
      </section>
      <section id="tire-location" className="tire-section tire-location">
        <div><h2>Адрес и телефон</h2><address>{TIRE_SERVICE.address}</address></div>
        <div className="tire-contact-details">
          <a className="tire-phone" href={TIRE_SERVICE.phoneHref}>{TIRE_SERVICE.phoneDisplay}</a>
          <p>Уточните время работы по телефону.</p>
          <div className="tire-contact-links">
            <a className="tire-button tire-button-primary" href={TIRE_SERVICE.yandexRouteUrl} target="_blank" rel="noopener noreferrer">Построить маршрут <span aria-hidden="true">↗</span></a>
            <a className="tire-route-link" href={TIRE_SERVICE.yandexMapsUrl} target="_blank" rel="noopener noreferrer">Карточка в Яндекс Картах <span aria-hidden="true">↗</span></a>
          </div>
        </div>
      </section>
      </main>
      <footer className="tire-footer"><div><a className="tire-brand" href="#tire-top">PG<span>Пушкинские<br />Горы</span></a><p>Независимый портал посёлка</p></div><nav aria-label="Ссылки внизу страницы"><Link to="/map">Карта</Link><Link to="/events">Афиша</Link><Link to="/services">Услуги посёлка</Link><Link to="/cabinet">Кабинет</Link></nav>
        <details className="tire-photo-credits"><summary>Источники фотографий</summary><p><a href="https://commons.wikimedia.org/wiki/File:Car_tire_closeup_1_2019-01-15.jpg" target="_blank" rel="noopener noreferrer">Протектор шины, Fastily, Wikimedia Commons</a>, CC BY-SA 4.0.</p><p><a href="https://commons.wikimedia.org/wiki/File:Михайловское._Разлив_реки_Сороть.jpg" target="_blank" rel="noopener noreferrer">Михайловское, Sea Est</a>, CC BY-SA 4.0. Фотографии уменьшены, преобразованы в WebP и кадрируются на странице. <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener noreferrer">Лицензия оригиналов и производных изображений</a>.</p></details>
      </footer>
    </div>
  );
}
