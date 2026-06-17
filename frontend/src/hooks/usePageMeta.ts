import { useEffect } from "react";

export function usePageMeta(description?: string) {
  useEffect(() => {
    if (!description) return undefined;

    let meta = document.querySelector('meta[name="description"]');
    const created = !meta;
    const previous = meta?.getAttribute("content") ?? "";

    if (!meta) {
      meta = document.createElement("meta");
      meta.setAttribute("name", "description");
      document.head.appendChild(meta);
    }

    meta.setAttribute("content", description);
    return () => {
      if (!meta) return;
      if (created) {
        meta.remove();
        return;
      }
      meta.setAttribute("content", previous);
    };
  }, [description]);
}
