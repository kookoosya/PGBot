#!/usr/bin/env node
/** Run export-places-backup-remote.sh on VPS. */
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

const require = createRequire(import.meta.url);
const { Client } = require("ssh2");

const password = process.env.DEPLOY_SSH_PASSWORD || process.env.VPS_PASSWORD || "";
const script = readFileSync(join(root, "scripts/export-places-backup-remote.sh"), "utf8");

const conn = new Client();
conn
  .on("ready", () => {
    conn.exec("bash -s", (err, stream) => {
      if (err) throw err;
      stream.write(script);
      stream.end();
      stream.on("data", (d) => process.stdout.write(d));
      stream.stderr.on("data", (d) => process.stderr.write(d));
      stream.on("close", (code) => {
        conn.end();
        process.exit(code ?? 0);
      });
    });
  })
  .on("error", (e) => {
    console.error(e.message);
    process.exit(1);
  })
  .connect({
    host: process.env.VPS_HOST || "192.210.213.135",
    username: process.env.VPS_USER || "root",
    password,
    readyTimeout: 90000,
  });
