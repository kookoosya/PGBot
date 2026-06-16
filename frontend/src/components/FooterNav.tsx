import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { BRAND } from "@/lib/branding";
import { MAIN_SECTIONS } from "@/lib/navigation";

export function FooterNav() {
  const [vkUrl, setVkUrl] = useState<string | null>(null);

  useEffect(() => {
    api.getPublicInfo().then((info) => setVkUrl(info.vk_url)).catch(() => {});
  }, []);

  const footerSections = MAIN_SECTIONS.filter((section) => section.to !== "/");

  return (
    <nav className="footer-nav" aria-label="Разделы портала">
      <div className="footer-nav-grid">
        {footerSections.map((section) => (
          <Link key={section.to} to={section.to} className="footer-nav-link no-underline">
            {section.icon} {section.label}
          </Link>
        ))}
        <Link to="/cabinet" className="footer-nav-link no-underline">
          👤 Кабинет
        </Link>
        {vkUrl && (
          <a
            href={vkUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="footer-nav-link no-underline"
          >
            📱 VK
          </a>
        )}
      </div>
      <p className="footer-nav-tagline m-0 text-sm text-muted-foreground">
        {BRAND.tagline} · {BRAND.district}
      </p>
    </nav>
  );
}
