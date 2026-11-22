import { useState } from "react";
import { Link } from "react-router-dom";
import { TodayInVillage } from "@/components/TodayInVillage";
import { UpcomingEvents } from "@/components/UpcomingEvents";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";
import {
  formatRubles,
  REMOVAL_INSTALLATION,
  ROSSVIK_VIDEOS,
  STUDDING,
  TIRE_SERVICE,
  TIRE_SIZE_PRICES,
  TUBE_REPAIR,
  TUBELESS_REPAIR,
  type ServicePrice,
} from "@/lib/tireService";
import "@/styles/tire-service.css";

type PriceTab = "mount" | "repair" | "tube" | "studding";
const PRICE_TABS: { id: PriceTab; label: string }[] = [
  { id: "mount", label: "Перебортовка" },
  { id: "repair", label: "Ремонт шин" },
  { id: "tube", label: "Ремонт камер" },
  { id: "studding", label: "Дошиповка" },
];

const VILLAGE_LINKS = [
  { to: "/map", label: "Карта и места", sub: "Найти нужное в посёлке", icon: "↗" },
  { to: "/events", label: "Афиша", sub: "События и мероприятия", icon: "↗" },
  { to: "/classifieds", label: "Объявления", sub: "Предложения жителей", icon: "↗" },
  { to: "/jobs", label: "Работа", sub: "Вакансии и предложения", icon: "↗" },
  { to: "/services", label: "Услуги", sub: "Местные специалисты", icon: "↗" },
  { to: "/complaints", label: "Обращения", sub: "Заявки и проблемы", icon: "↗" },
];

function PriceRows({ items }: { items: readonly ServicePrice[] }) {
  return (
    <div className="tire-service-rows">
      {items.map((item) => (
        <div className="tire-service-row" key={item.name}>
          <span>{item.name}</span>
          <strong>{item.price}</strong>
        </div>
      ))}
    </div>
  );
}

export function TireServiceLanding() {
  const [tab, setTab] = useState<PriceTab>("mount");
  const [selectedSize, setSelectedSize] = useState("R16");
  const selected = TIRE_SIZE_PRICES.find((item) => item.size === selectedSize) ?? TIRE_SIZE_PRICES[4];

  return (
    <div className="tire-landing">
      <section className="tire-hero" id="tire-top" aria-labelledby="tire-hero-title">
        <div className="tire-hero-noise" aria-hidden="true" />
        <div className="tire-hero-content">
          <div className="tire-overline"><span className="tire-overline-dot" /> ПУШКИНСКИЕ ГОРЫ · АЭРОДРОМНАЯ, 23</div>
          <p className="tire-hero-index">МАСТЕРСКАЯ ПО РЕМОНТУ И ОБСЛУЖИВАНИЮ ШИН</p>
          <h1 id="tire-hero-title">Дорога<br />начинается<br /><em>с колёс.</em></h1>
          <p className="tire-hero-description">Шиномонтаж, балансировка, ремонт проколов и порезов, дошиповка. Услуги и цены — без догадок: весь прайс открыт на этой странице.</p>
          <div className="tire-hero-actions">
            <a className="tire-button tire-button-primary" href="#tire-prices">Узнать стоимость <span aria-hidden="true">↗</span></a>
            <a className="tire-button tire-button-outline" href={TIRE_SERVICE.phoneHref}>Позвонить <span aria-hidden="true">↗</span></a>
          </div>
          <p className="tire-hero-footnote">Материалы ROSSVIK · Снятие и установка колёс оплачиваются отдельно</p>
        </div>
        <div className="tire-hero-visual" aria-hidden="true">
          <div className="tire-visual-orbit tire-visual-orbit-one" />
          <div className="tire-visual-orbit tire-visual-orbit-two" />
          <div className="tire-visual-wheel"><div className="tire-visual-rim"><div className="tire-visual-hub" /></div></div>
          <span className="tire-visual-word">SERVICE / 2026</span>
        </div>
        <div className="tire-hero-bottom">
          <a href="#tire-services" className="tire-scroll-down">Листайте вниз <span aria-hidden="true">↓</span></a>
          <a href={TIRE_SERVICE.yandexMapsUrl} target="_blank" rel="noopener noreferrer">Найти на Яндекс Картах ↗</a>
        </div>
      </section>

      <nav className="tire-page-nav" aria-label="Разделы главной страницы">
        <a href="#tire-services">Услуги</a>
        <a href="#tire-prices">Прайс</a>
        <a href="#tire-methods">Как ремонтируют</a>
        <a href="#tire-location">Контакты</a>
        <a href="#village">Пушкинские Горы</a>
      </nav>

      <section id="tire-services" className="tire-section tire-section-light">
        <div className="tire-section-heading">
          <span className="tire-eyebrow">01 / Мастерская</span>
          <h2>Когда важно<br /><em>сцепление с дорогой.</em></h2>
          <p>Реальный перечень работ из действующего прайса. Без несуществующих услуг и обещаний.</p>
        </div>
        <div className="tire-services-grid">
          <a href="#tire-prices" onClick={() => setTab("mount")} className="tire-service-card tire-service-card-feature">
            <span className="tire-card-num">01 — ШИНОМОНТАЖ</span>
            <span className="tire-service-icon" aria-hidden="true">◉</span>
            <h3>Переобуть<br />автомобиль</h3>
            <p>Разборка, сборка, балансировка. От R12 до R20, а также УАЗ, микроавтобусы и Газель.</p>
            <span className="tire-card-cta">Посмотреть тарифы ↗</span>
          </a>
          <a href="#tire-prices" onClick={() => setTab("repair")} className="tire-service-card">
            <span className="tire-card-num">02 — РЕМОНТ</span>
            <span className="tire-service-icon" aria-hidden="true">✳</span>
            <h3>Ремонт<br />повреждений</h3>
            <p>Проколы, порезы, проверка герметичности и вулканизация — по результату осмотра.</p>
            <span className="tire-card-cta">Перейти к ценам ↗</span>
          </a>
          <a href="#tire-prices" onClick={() => setTab("studding")} className="tire-service-card">
            <span className="tire-card-num">03 — ЗИМНИЕ ШИНЫ</span>
            <span className="tire-service-icon" aria-hidden="true">✦</span>
            <h3>Дошиповка<br />шин</h3>
            <p>Установка ремонтных шипов и удаление старых. Цена указана за штуку.</p>
            <span className="tire-card-cta">Посмотреть тарифы ↗</span>
          </a>
          <a href="#tire-prices" onClick={() => setTab("tube")} className="tire-service-card">
            <span className="tire-card-num">04 — КАМЕРЫ</span>
            <span className="tire-service-icon" aria-hidden="true">◎</span>
            <h3>Ремонт<br />камер</h3>
            <p>Проколы, порезы, вклейка вентиля для легковых и грузовых камер.</p>
            <span className="tire-card-cta">Перейти к ценам ↗</span>
          </a>
        </div>
      </section>

      <section id="tire-prices" className="tire-section tire-pricing">
        <div className="tire-section-heading tire-heading-dark">
          <span className="tire-eyebrow">02 / Цены без сюрпризов</span>
          <h2>Открытый<br /><em>прайс-лист.</em></h2>
          <p>Редакция от {TIRE_SERVICE.priceRevision}. Для комплекта действует цена из прайса, а не арифметическая сумма отдельных колёс.</p>
        </div>

        <div className="tire-price-panel">
          <div className="tire-price-tabs" role="tablist" aria-label="Категория услуг">
            {PRICE_TABS.map((item) => (
              <button
                key={item.id}
                type="button"
                id={`tire-tab-${item.id}`}
                role="tab"
                aria-selected={tab === item.id}
                aria-controls="tire-tab-panel"
                className={tab === item.id ? "is-active" : ""}
                onClick={() => setTab(item.id)}
              >{item.label}</button>
            ))}
          </div>
          <div id="tire-tab-panel" role="tabpanel" aria-labelledby={`tire-tab-${tab}`}>
            {tab === "mount" ? (
              <>
                <p className="tire-price-label">ПОДБЕРИТЕ РАЗМЕР КОЛЕСА</p>
                <div className="tire-size-picker">
                  {TIRE_SIZE_PRICES.map((item) => (
                    <button key={item.size} type="button" aria-pressed={selectedSize === item.size} className={selectedSize === item.size ? "is-selected" : ""} onClick={() => setSelectedSize(item.size)}>{item.size}</button>
                  ))}
                </div>
                <div className="tire-price-summary">
                  <div><span>ОДНО КОЛЕСО · {selected.size}</span><strong>{formatRubles(selected.wheel)}</strong></div>
                  <div className="tire-price-summary-highlight"><span>КОМПЛЕКТ · {selected.setCount} ШТ.</span><strong>{formatRubles(selected.set)}</strong></div>
                </div>
                <details className="tire-price-breakdown">
                  <summary>Показать детализацию цены <span>+</span></summary>
                  <div className="tire-service-rows">
                    <div className="tire-service-row"><span>Разборка (1 колесо)</span><strong>{formatRubles(selected.dismount)}</strong></div>
                    <div className="tire-service-row"><span>Сборка (1 колесо)</span><strong>{formatRubles(selected.mount)}</strong></div>
                    <div className="tire-service-row"><span>Балансировка (1 колесо)</span><strong>{formatRubles(selected.balance)}</strong></div>
                  </div>
                </details>
                <div className="tire-price-secondary">
                  <h3>Снятие и установка колёс</h3>
                  <PriceRows items={REMOVAL_INSTALLATION} />
                  <p className="tire-price-note">Снятие и установка оплачиваются отдельно от перебортовки. Грузики включены в цену перебортовки. Единицу тарификации снятия и установки уточняйте при обращении.</p>
                </div>
              </>
            ) : tab === "repair" ? (
              <>
                <p className="tire-price-label">РЕМОНТ БЕСКАМЕРНЫХ ШИН</p>
                <PriceRows items={TUBELESS_REPAIR} />
                <p className="tire-price-note">Цена ремонта зависит от размера латки, размера шины и характера повреждения.</p>
              </>
            ) : tab === "tube" ? (
              <>
                <p className="tire-price-label">РЕМОНТ КАМЕР</p>
                <PriceRows items={TUBE_REPAIR} />
              </>
            ) : (
              <>
                <p className="tire-price-label">ОШИПОВКА / ДОШИПОВКА</p>
                <PriceRows items={STUDDING} />
              </>
            )}
          </div>
          <div className="tire-price-footer">
            <span>Стоимость конкретного ремонта уточняется после оценки повреждения.</span>
            <a href={TIRE_SERVICE.phoneHref}>Уточнить по телефону ↗</a>
          </div>
        </div>
      </section>

      <section id="tire-methods" className="tire-section tire-methods">
        <div className="tire-section-heading">
          <span className="tire-eyebrow">03 / Материалы и технология</span>
          <h2>Не магия.<br /><em>Технология.</em></h2>
          <p>В работе используются материалы ROSSVIK. Ниже — обучающие видеоматериалы производителя, чтобы было понятно, как устроены разные виды ремонта. Это не съёмки нашей мастерской.</p>
        </div>
        <div className="tire-methods-grid">
          {ROSSVIK_VIDEOS.map((video, index) => (
            <a key={video.url} className="tire-method-card" href={video.url} target="_blank" rel="noopener noreferrer">
              <span className="tire-method-index">0{index + 1} / {video.service}</span>
              <span className="tire-method-play" aria-hidden="true">↗</span>
              <h3>{video.title}</h3>
              <span className="tire-method-source">Обучающий материал · {video.source}</span>
            </a>
          ))}
        </div>
      </section>

      <section id="tire-location" className="tire-section tire-location">
        <div className="tire-location-main">
          <span className="tire-eyebrow">04 / Как нас найти</span>
          <h2>Заезжайте.<br /><em>Мы на карте.</em></h2>
          <address>{TIRE_SERVICE.address}</address>
          <a href={TIRE_SERVICE.phoneHref} className="tire-location-phone">{TIRE_SERVICE.phoneDisplay}</a>
          <div className="tire-location-actions">
            <a href={TIRE_SERVICE.yandexMapsUrl} target="_blank" rel="noopener noreferrer" className="tire-button tire-button-primary">Открыть Яндекс Карты ↗</a>
            <a href={TIRE_SERVICE.phoneHref} className="tire-button tire-button-outline">Позвонить ↗</a>
          </div>
          <p>Актуальное время работы и маршрут уточняйте в карточке организации на Яндекс Картах.</p>
        </div>
        <a className="tire-location-map" href={TIRE_SERVICE.yandexMapsUrl} target="_blank" rel="noopener noreferrer" aria-label="Открыть расположение шиномонтажа на Яндекс Картах">
          <div className="tire-map-grid" aria-hidden="true" />
          <div className="tire-map-pin" aria-hidden="true">●</div>
          <strong>Пушкинские Горы</strong>
          <span>Аэродромная, 23</span>
          <small>Построить маршрут ↗</small>
        </a>
      </section>

      <section id="village" className="tire-section tire-village">
        <div className="tire-section-heading tire-village-heading">
          <span className="tire-eyebrow">05 / Не только мастерская</span>
          <h2>Пушкинские Горы.<br /><em>Место, где мы живём.</em></h2>
          <p>Афиша, карта, объявления, вакансии и полезные сервисы посёлка — в том же проекте PG. Все существующие разделы портала остаются доступны.</p>
        </div>
        <div className="tire-village-links">
          {VILLAGE_LINKS.map((item, index) => (
            <Link to={item.to} key={item.to} className="tire-village-link">
              <span className="tire-village-link-index">0{index + 1}</span>
              <span className="tire-village-link-copy"><strong>{item.label}</strong><small>{item.sub}</small></span>
              <span className="tire-village-link-arrow" aria-hidden="true">{item.icon}</span>
            </Link>
          ))}
        </div>
        <div className="tire-village-live">
          <div className="tire-village-live-card"><TodayInVillage /></div>
          <div className="tire-village-live-card"><UpcomingEvents variant="landing" /></div>
        </div>
        <p className="tire-village-footnote">{LANDING_SECTIONS.useful.title} — <Link to="/map">перейти к карте посёлка ↗</Link></p>
      </section>

      <div className="tire-endnote">
        <span>PG / ПУШКИНСКИЕ ГОРЫ</span>
        <a href="#tire-top">Наверх ↑</a>
      </div>
    </div>
  );
}
