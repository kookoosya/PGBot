import { useState } from "react";
import { LiterarySectionHead } from "@/components/literary";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";
import { PHOTO_VERSES, VILLAGE_PHOTOS } from "@/lib/pushkin";

const copy = LANDING_SECTIONS.gallery;

export function VillageGallery() {
  const [broken, setBroken] = useState<Record<string, boolean>>({});

  return (
    <section className="literary-gallery-section">
      <div className="page-section max-w-5xl mx-auto">
        <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-8">
          {VILLAGE_PHOTOS.map((photo, i) => (
            <article key={photo.title} className="literary-gallery-card group">
              <div className="literary-gallery-photo aspect-[4/3] overflow-hidden bg-muted relative">
                {!broken[photo.title] ? (
                  <picture>
                    <source srcSet={photo.webp} type="image/webp" />
                    <img
                      src={photo.url}
                      alt={photo.title}
                      className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]"
                      loading={i < 2 ? "eager" : "lazy"}
                      decoding="async"
                      fetchPriority={i < 2 ? "high" : "low"}
                      width={720}
                      height={540}
                      onError={() => setBroken((b) => ({ ...b, [photo.title]: true }))}
                    />
                  </picture>
                ) : (
                  <div className="h-full w-full bg-muted flex items-center justify-center text-sm text-muted-foreground px-4 text-center">
                    Фото временно недоступно
                  </div>
                )}
                <div className="literary-gallery-scrim" aria-hidden />
              </div>
              <div className="literary-gallery-caption">
                <h4 className="literary-gallery-title">{photo.title}</h4>
                <p className="literary-gallery-sub">{photo.caption}</p>
                {PHOTO_VERSES[photo.title] && (
                  <p className="literary-gallery-verse">{PHOTO_VERSES[photo.title]}</p>
                )}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
