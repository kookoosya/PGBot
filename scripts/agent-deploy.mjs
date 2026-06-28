#!/usr/bin/env node
/**
 * Agent deploy: Cloudflare DNS only (RU) + git pull + vps-deploy.sh on VPS.
 * Usage: DEPLOY_SSH_PASSWORD=*** node scripts/agent-deploy.mjs
 * Or create .deploy.env (see .deploy.env.example)
 */
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const envFile = join(root, ".deploy.env");
if (existsSync(envFile)) {
  for (const line of readFileSync(envFile, "utf8").split("\n")) {
    const m = line.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

// DNS only first — required for Russia (Cloudflare Proxied throttled since 2025)
if (process.env.CF_API_TOKEN || process.env.CLOUDFLARE_API_TOKEN) {
  const { spawnSync } = await import("node:child_process");
  const r = spawnSync(process.execPath, [join(root, "scripts/cloudflare-dns-only.mjs")], {
    stdio: "inherit",
    env: process.env,
  });
  if (r.status !== 0) console.warn("cloudflare-dns-only warning (continuing deploy)");
}

const require = createRequire(import.meta.url);
const ssh2Paths = [
  join(dirname(fileURLToPath(import.meta.url)), "../../GMX - Replay/Backend/node_modules/ssh2"),
  join(dirname(fileURLToPath(import.meta.url)), "../../node_modules/ssh2"),
  "ssh2",
];
let Client;
for (const p of ssh2Paths) {
  try {
    Client = require(p).Client;
    break;
  } catch {
    /* try next */
  }
}
if (!Client) {
  console.error("ssh2 not found — npm install ssh2 in PGBot or use GMX Backend node_modules");
  process.exit(1);
}

const password = process.env.DEPLOY_SSH_PASSWORD || process.env.VPS_PASSWORD || process.env.SSHPASS || "";
const host = process.env.VPS_HOST || "192.210.213.135";
const user = process.env.VPS_USER || "root";
const branch = process.env.BRANCH || "main";
const maxAttempts = Number(process.env.DEPLOY_ATTEMPTS || 12);

const remote = `
set -e
cd /opt/pgbot
git fetch origin ${branch}
git checkout ${branch}
git pull origin ${branch}
bash scripts/vps-deploy.sh
bash scripts/setup-ru-direct-dns-check.sh || true
bash scripts/smoke-public.sh https://pushkinskie-gory.xyz || true
`;

function sshOnce() {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn
      .on("ready", () => {
        conn.exec(remote, (err, stream) => {
          if (err) {
            conn.end();
            reject(err);
            return;
          }
          stream.on("data", (d) => process.stdout.write(d));
          stream.stderr.on("data", (d) => process.stderr.write(d));
          stream.on("close", (code) => {
            conn.end();
            if (code === 0) resolve(0);
            else reject(new Error(`remote exit ${code}`));
          });
        });
      })
      .on("error", reject)
      .connect({ host, username: user, password, readyTimeout: 90000 });
  });
}

async function main() {
  if (!password) {
    console.error("Set DEPLOY_SSH_PASSWORD or VPS_PASSWORD");
    process.exit(1);
  }
  for (let i = 1; i <= maxAttempts; i++) {
    console.log(`=== deploy attempt ${i} ===`);
    try {
      await sshOnce();
      console.log("Deploy OK");
      return;
    } catch (e) {
      console.error(String(e.message || e));
      if (i === maxAttempts) process.exit(1);
      await new Promise((r) => setTimeout(r, 5000));
    }
  }
}

main();
