#!/usr/bin/env node
/**
 * Cloudflare: switch @ and www A records to DNS only (required for Russia since 2025).
 * Usage: CF_API_TOKEN=*** node scripts/cloudflare-dns-only.mjs
 */
const DOMAIN = process.env.DOMAIN || "pushkinskie-gory.xyz";
const ORIGIN_IP = process.env.ORIGIN_IP || "192.210.213.135";
const token = process.env.CF_API_TOKEN || process.env.CLOUDFLARE_API_TOKEN || "";

if (!token) {
  console.log("SKIP: set CF_API_TOKEN (Cloudflare → My Profile → API Tokens → Edit zone DNS)");
  process.exit(0);
}

async function cf(path, opts = {}) {
  const res = await fetch(`https://api.cloudflare.com/client/v4${path}`, {
    ...opts,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  const data = await res.json();
  if (!data.success) throw new Error(JSON.stringify(data.errors || data));
  return data;
}

async function main() {
  let zoneId = process.env.CF_ZONE_ID || "";
  if (!zoneId) {
    const zones = await cf(`/zones?name=${DOMAIN}`);
    zoneId = zones.result[0]?.id;
  }
  if (!zoneId) throw new Error(`zone not found: ${DOMAIN}`);

  for (const name of [DOMAIN, `www.${DOMAIN}`]) {
    const list = await cf(`/zones/${zoneId}/dns_records?type=A&name=${encodeURIComponent(name)}`);
    const rec = list.result[0];
    if (!rec) {
      console.log(`WARN: no A record for ${name}`);
      continue;
    }
    await cf(`/zones/${zoneId}/dns_records/${rec.id}`, {
      method: "PATCH",
      body: JSON.stringify({
        type: "A",
        name,
        content: ORIGIN_IP,
        proxied: false,
        ttl: 300,
      }),
    });
    console.log(`OK DNS only: ${name} → ${ORIGIN_IP}`);
  }

  // verify public DNS (may take a few minutes to propagate)
  const resolved = await fetch(`https://dns.google/resolve?name=${DOMAIN}&type=A`)
    .then((r) => r.json())
    .catch(() => null);
  const ips = resolved?.Answer?.map((a) => a.data).filter(Boolean) || [];
  console.log(`Public A: ${ips.join(", ") || "pending"}`);
  if (ips.some((ip) => ip.startsWith("104.") || ip.startsWith("172.67."))) {
    console.log("WARN: still Cloudflare Proxied IPs — wait 5–15 min for DNS propagation");
  } else if (ips.includes(ORIGIN_IP)) {
    console.log("OK: direct to VPS — should work in Russia");
  }
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
