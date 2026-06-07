import { useLocation } from "react-router-dom";
import { quoteForPage } from "@/lib/pushkin";

export function PushkinBanner() {
  const { pathname } = useLocation();
  const quote = quoteForPage(pathname);

  return (
    <div className="pushkin-quote-banner mx-auto max-w-6xl px-4 py-3">
      <p className="text-center font-serif italic text-base md:text-lg whitespace-pre-line">
        {quote}
      </p>
    </div>
  );
}
