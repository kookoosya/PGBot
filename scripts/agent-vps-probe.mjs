#!/usr/bin/env node
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { Client } = require("C:/Users/user/Desktop/GMX - Replay/Backend/node_modules/ssh2");

const password = process.env.DEPLOY_SSH_PASSWORD || process.env.VPS_PASSWORD || "";
const cmd = `
echo '=== local health ==='
curl -sS --max-time 10 http://127.0.0.1:8088/health || echo FAIL
echo
curl -sS --max-time 10 -o /dev/null -w 'local info:%{http_code}\\n' http://127.0.0.1:8088/api/v1/public/info
echo '=== via domain from VPS ==='
curl -sS --max-time 10 -o /dev/null -w 'domain health:%{http_code}\\n' https://pushkinskie-gory.xyz/health
curl -sS --max-time 10 http://192.210.213.135/health -k -o /dev/null -w 'direct ip health:%{http_code}\\n' || true
echo '=== docker ==='
docker compose -f /opt/pgbot/docker-compose.prod.yml ps --format '{{.Name}} {{.Status}}'
echo '=== backend logs ==='
docker compose -f /opt/pgbot/docker-compose.prod.yml logs backend --tail 15 2>&1
echo '=== cf env ==='
grep -iE 'CF_|CLOUDFLARE' /opt/pgbot/.env 2>/dev/null || echo 'no cf token in .env'
echo '=== DNS ==='
dig +short pushkinskie-gory.xyz A | head -3
`;

const conn = new Client();
conn
  .on("ready", () => {
    conn.exec(cmd, (err, stream) => {
      if (err) throw err;
      stream.on("data", (d) => process.stdout.write(d));
      stream.stderr.on("data", (d) => process.stderr.write(d));
      stream.on("close", () => conn.end());
    });
  })
  .on("error", (e) => {
    console.error(e.message);
    process.exit(1);
  })
  .connect({ host: "192.210.213.135", username: "root", password, readyTimeout: 90000 });
