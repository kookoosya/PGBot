import { VILLAGE_PHOTOS } from "@/lib/pushkin";

export function VillageGallery() {
  return (
    <section className="section-alt">
      <div className="page-section">
      <h3 className="section-title">Пушкиногорье</h3>
      <p className="text-center text-muted-foreground -mt-6 mb-10 text-sm">Земля, где жил и творил поэт</p>
      <div className="grid gap-4 md:grid-cols-3">
        {VILLAGE_PHOTOS.map((photo) => (
          <div key={photo.title} className="pushkin-card-hover overflow-hidden group">
            <div className="aspect-[4/3] overflow-hidden bg-muted">
              <img
                src={photo.url}
                alt={photo.title}
                className="h-full w-full object-cover transition group-hover:scale-105"
                loading="lazy"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
            <div className="p-4">
              <h4 className="font-semibold">{photo.title}</h4>
              <p className="text-xs text-muted-foreground">{photo.caption}</p>
            </div>
          </div>
        ))}
      </div>
      </div>
    </section>
  );
}
