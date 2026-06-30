#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const ssh2Paths = [
  join(root, "../../GMX - Replay/Backend/node_modules/ssh2"),
  join(root, "node_modules/ssh2"),
  "ssh2",
];
let Client;
for (const p of ssh2Paths) {
  try {
    Client = require(p).Client;
    break;
  } catch {
    /* next */
  }
}
if (!Client) {
  console.error("ssh2 not found");
  process.exit(1);
}

const host = process.env.RU_VPS_HOST || "185.103.109.79";
const password = process.env.RU_VPS_PASSWORD || process.env.DEPLOY_SSH_PASSWORD || "";
if (!password) {
  console.error("Set RU_VPS_PASSWORD");
  process.exit(1);
}

const script = readFileSync(join(root, "scripts/_ru-proxy-setup-remote.sh"), "utf8");

function sshExec(cmd) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    conn
      .on("ready", () => {
        conn.exec(cmd, (err, stream) => {
          if (err) {
            conn.end();
            reject(err);
            return;
          }
          let out = "";
          stream.on("data", (d) => {
            out += d;
            process.stdout.write(d);
          });
          stream.stderr.on("data", (d) => process.stderr.write(d));
          stream.on("close", (code) => {
            conn.end();
            code ? reject(new Error(`exit ${code}`)) : resolve(out);
          });
        });
      })
      .on("error", reject)
      .connect({
        host,
        port: 22,
        username: "root",
        password,
        readyTimeout: 60000,
        tryKeyboard: true,
      });
  });
}

await sshExec(`bash -s <<'REMOTE'\n${script}\nREMOTE`);
console.log("\nRU proxy HTTP ready on", host);
