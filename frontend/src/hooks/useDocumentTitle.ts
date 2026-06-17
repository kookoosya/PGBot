import { useEffect } from "react";

const SITE_TITLE = "Пушкинские Горы";

export function useDocumentTitle(pageTitle?: string) {
  useEffect(() => {
    const previous = document.title;
    document.title = pageTitle ? `${pageTitle} — ${SITE_TITLE}` : SITE_TITLE;
    return () => {
      document.title = previous;
    };
  }, [pageTitle]);
}
