import { LANDING_VERSES } from "@/lib/pushkin";

export function PushkinVersesSection() {
  return (
    <section className="epic-verses-section" aria-labelledby="verses-title">
      <div className="page-section">
        <div className="epic-section-head">
          <p className="epic-section-kicker">А.С. Пушкин</p>
          <h2 id="verses-title" className="epic-section-title">
            Строки о родной земле
          </h2>
          <p className="epic-section-desc">
            Посёлок — в сердце Пушкиногорья. Разделы портала — во вкладках сверху и снизу экрана.
          </p>
        </div>
        <div className="epic-verses-grid">
          {LANDING_VERSES.map((verse) => (
            <figure key={verse.source + verse.text.slice(0, 24)} className="epic-verse-card">
              <blockquote className="epic-verse-text">{verse.text}</blockquote>
              <figcaption className="epic-verse-source">— {verse.source}</figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
