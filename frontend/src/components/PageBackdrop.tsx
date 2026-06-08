import { useLocation } from "react-router-dom";
import { wallpaperForPath } from "@/lib/pageWallpapers";

export function PageBackdrop() {
  const { pathname } = useLocation();
  const wp = wallpaperForPath(pathname);

  if (pathname === "/" || pathname === "") {
    return null;
  }

  return (
    <div className="page-backdrop" aria-hidden>
      <picture>
        <source srcSet={wp.webp} type="image/webp" />
        <img src={wp.url} alt="" className="page-backdrop-img" loading="lazy" decoding="async" />
      </picture>
      <div className="page-backdrop-scrim" />
      <div className="page-backdrop-vignette" />
    </div>
  );
}
