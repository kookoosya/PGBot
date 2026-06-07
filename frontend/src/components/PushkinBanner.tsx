import { useLocation } from "react-router-dom";
import { quoteForPage } from "@/lib/pushkin";

export function PushkinBanner() {
  const { pathname } = useLocation();
  const quote = quoteForPage(pathname);

  return (
    <div className="pushkin-quote-banner px-4 py-3">
      <p className="text-center font-serif italic text-sm md:text-base leading-relaxed whitespace-pre-line">
        {quote}
      </p>
    </div>
  );
}
