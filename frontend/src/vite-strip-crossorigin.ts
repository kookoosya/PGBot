import type { Plugin } from "vite";

/** Vite ставит crossorigin на CSS/JS — без ACAO браузер может не применить стили. */
export function stripCrossorigin(): Plugin {
  return {
    name: "strip-crossorigin",
    enforce: "post",
    transformIndexHtml(html) {
      return html.replace(/\s+crossorigin/g, "");
    },
  };
}
