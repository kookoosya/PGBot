import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { createServer } from "vite";

// Execute the same homepage component at build time. Effects and API calls do not run.
const server = await createServer({ server: { middlewareMode: true }, appType: "custom" });
try {
  const { getHomeStructuredData, renderHome } = await server.ssrLoadModule("/src/prerender.tsx");
  const target = resolve("dist/index.html");
  const template = await readFile(target, "utf8");
  const marker = '<div id="root"></div>';
  if (!template.includes(marker)) throw new Error("Homepage root marker missing");
  // Nested SPA URLs get an empty application shell with neutral metadata.
  const spa = template
    .replace(/^\s*<link rel="preload" as="image"[^>]*>/m, "")
    .replace(/^\s*<meta property="og:[^"]+"[^>]*>/gm, "")
    .replace(/<meta name="description"[^>]*>/, '<meta name="description" content="Независимый портал Пушкинских Гор." />')
    .replace(/<title>[^<]+<\/title>/, "<title>Пушкинские Горы | PG</title>");
  let html = template.replace(marker, () => `<div id="root" data-prerendered>${renderHome()}</div>`);
  const publicUrl = process.env.PG_PUBLIC_URL;
  let robots = "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /cabinet\nDisallow: /official\n";
  if (publicUrl) {
    const url = new URL(publicUrl);
    if (url.protocol !== "https:" || url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
      throw new Error("PG_PUBLIC_URL must be an HTTPS origin without credentials, path, query or fragment");
    }
    const origin = url.origin;
    const workshop = JSON.stringify(getHomeStructuredData(`${origin}/`)).replaceAll("<", "\\u003c");
    html = html.replace("</head>", () => `<link rel="canonical" href="${origin}/" /><meta property="og:url" content="${origin}/" /><meta property="og:image" content="${origin}/images/pg/tire-1280.webp" /><script type="application/ld+json">${workshop}</script></head>`);
    await writeFile(resolve("dist/sitemap.xml"), `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>${origin}/</loc></url></urlset>`);
    robots += `Sitemap: ${origin}/sitemap.xml\n`;
  }
  await writeFile(target, html);
  await writeFile(resolve("dist/spa.html"), spa);
  await writeFile(resolve("dist/robots.txt"), robots);
  console.log(`Homepage prerendered (${Buffer.byteLength(html)} bytes), public domain ${publicUrl ? "configured" : "pending"}`);
} finally {
  await server.close();
}
