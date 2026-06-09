import { quoteForPage } from "@/lib/pushkin";

export function FooterNav() {
  const quote = quoteForPage("/");

  return (
    <div className="footer-minimal">
      <p className="pushkin-quote-footer whitespace-pre-line">{quote}</p>
    </div>
  );
}
