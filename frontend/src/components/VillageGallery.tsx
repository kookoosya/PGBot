import { useState } from "react";
import { PHOTO_VERSES, VILLAGE_PHOTOS } from "@/lib/pushkin";

export function VillageGallery() {
  const [broken, setBroken] = useState<Record<string, boolean>>({});

  return (
    <section className="section-alt">
      <div className="page-section">
        <h3 className="section-title">Пушкиногорье</h3>
        <p className="text-center text-muted-foreground -mt-6 mb-10 text-sm">
          Музей-заповедник, монастырь, усадьбы — места, где жил и творил поэт
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {VILLAGE_PHOTOS.map((photo, i) => (
            <div key={photo.title} className="pushkin-card-hover overflow-hidden group">
              <div className="aspect-[4/3] overflow-hidden bg-muted relative">
                {!broken[photo.title] ? (
                  <picture>
                    <source srcSet={photo.webp} type="image/webp" />
                    <img
                      src={photo.url}
                      alt={photo.title}
                      className="h-full w-full object-cover transition group-hover:scale-105"
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
              </div>
              <div className="p-4">
                <h4 className="font-semibold">{photo.title}</h4>
                <p className="text-xs text-muted-foreground">{photo.caption}</p>
                {PHOTO_VERSES[photo.title] && (
                  <p className="epic-photo-verse">{PHOTO_VERSES[photo.title]}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
