#!/usr/bin/env node
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { Client } = require("C:/Users/user/Desktop/GMX - Replay/Backend/node_modules/ssh2");

const password = process.env.DEPLOY_SSH_PASSWORD || "";
const cmd = `
set -e
cd /opt/pgbot
echo '=== git ==='
git rev-parse HEAD
echo '=== docker ps ==='
docker compose -f docker-compose.prod.yml ps
echo '=== backend logs ==='
docker compose -f docker-compose.prod.yml logs backend --tail 80
echo '=== alembic ==='
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || true
echo '=== restart backend ==='
docker compose -f docker-compose.prod.yml restart backend
sleep 8
curl -sS http://127.0.0.1:8088/health || true
echo
curl -sS https://pushkinskie-gory.xyz/health || true
echo
`;

const conn = new Client();
conn
  .on("ready", () => {
    conn.exec(cmd, (err, stream) => {
      if (err) throw err;
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
    username: "root",
    password,
    readyTimeout: 120000,
  });
