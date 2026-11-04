import http from "node:http";
import { DatabaseSync } from "node:sqlite";
import { randomBytes, createHash, scrypt, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";
import { pathToFileURL } from "node:url";

// Prototype-only: no public hosting, no original game API, no LIAPP modification.
const derive = promisify(scrypt);
const shaToken = value => createHash("sha256").update(Buffer.from(value, "hex")).digest("hex");
const bad = (status, message) => Object.assign(new Error(message), { status });
function reply(res, code, data) {
  res.writeHead(code, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "x-content-type-options": "nosniff"
  });
  res.end(JSON.stringify(data));
}
async function body(req) {
  if (!req.headers["content-type"]?.startsWith("application/json")) throw bad(415, "JSON_REQUIRED");
  const chunks = [];
  let bytes = 0;
  for await (const piece of req) {
    bytes += piece.length;
    if (bytes > 4096) throw bad(413, "REQUEST_TOO_LARGE");
    chunks.push(piece);
  }
  try {
    const obj = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) throw Error();
    return obj;
  } catch { throw bad(400, "INVALID_JSON"); }
}
export function createApp({ dbPath = ":memory:", requestLimit = 30 } = {}) {
  const db = new DatabaseSync(dbPath);
  db.exec("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;");
  db.exec("CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY,username TEXT NOT NULL UNIQUE COLLATE NOCASE,salt TEXT NOT NULL,pass_hash TEXT NOT NULL,created_at INTEGER NOT NULL);");
  db.exec("CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY,account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,expires_at INTEGER NOT NULL);");
  db.exec("CREATE INDEX IF NOT EXISTS session_expires ON sessions(expires_at);");
  const insertUser = db.prepare("INSERT INTO accounts(username,salt,pass_hash,created_at) VALUES(?,?,?,?)");
  const findUser = db.prepare("SELECT id,username,salt,pass_hash FROM accounts WHERE username=?");
  const newSession = db.prepare("INSERT INTO sessions(token_hash,account_id,expires_at) VALUES(?,?,?)");
  const lookupSession = db.prepare("SELECT a.id,a.username FROM sessions s JOIN accounts a ON a.id=s.account_id WHERE s.token_hash=? AND s.expires_at>?");
  const removeSession = db.prepare("DELETE FROM sessions WHERE token_hash=?");
  const visits = new Map();
  function throttle(req) {
    const addr = req.socket.remoteAddress || "unknown";
    const now = Date.now();
    let info = visits.get(addr);
    if (!info || now >= info.until) info = { count: 0, until: now + 60000 };
    info.count++;
    visits.set(addr, info);
    if (visits.size > 10000) visits.clear();
    if (info.count > requestLimit) throw bad(429, "RATE_LIMITED");
  }
  function auth(req) {
    const match = /^Bearer ([a-f0-9]{64})$/.exec(req.headers.authorization || "");
    if (!match) throw bad(401, "LOGIN_REQUIRED");
    const acc = lookupSession.get(shaToken(match[1]), Date.now());
    if (!acc) throw bad(401, "SESSION_EXPIRED");
    return { account: acc, token: match[1] };
  }
  const server = http.createServer(async (req, res) => {
    try {
      const path = new URL(req.url, "http://localhost").pathname;
      if (req.method === "GET" && path === "/health")
        return reply(res, 200, { ok: true, service: "slayer-login-v2" });
      if (req.method === "POST" && path === "/api/v1/auth/register") {
        throttle(req);
        const data = await body(req);
        const username = typeof data.username === "string" ? data.username.trim().toLowerCase() : "";
        const password = data.password;
        if (!/^[a-z0-9_]{3,24}$/.test(username) ||
            typeof password !== "string" || password.length < 12 || password.length > 128)
          throw bad(400, "INVALID_CREDENTIALS");
        if (findUser.get(username)) throw bad(409, "USERNAME_UNAVAILABLE");
        const salt = randomBytes(16);
        const secret = await derive(password, salt, 64);
        try {
          insertUser.run(username, salt.toString("hex"), secret.toString("hex"), Date.now());
        } catch (e) {
          if (e.code?.startsWith("SQLITE_CONSTRAINT")) throw bad(409, "USERNAME_UNAVAILABLE");
          throw e;
        }
        return reply(res, 201, { ok: true });
      }
      if (req.method === "POST" && path === "/api/v1/auth/login") {
        throttle(req);
        const data = await body(req);
        const username = typeof data.username === "string" ? data.username.trim().toLowerCase() : "";
        const password = data.password;
        if (!/^[a-z0-9_]{3,24}$/.test(username) ||
            typeof password !== "string" || password.length > 128)
          throw bad(401, "LOGIN_FAILED");
        const account = findUser.get(username);
        const salt = account ? Buffer.from(account.salt, "hex") : Buffer.alloc(16, 0);
        const expected = account ? Buffer.from(account.pass_hash, "hex") : Buffer.alloc(64, 0);
        const proof = await derive(password, salt, 64);
        if (!account || !timingSafeEqual(proof, expected)) throw bad(401, "LOGIN_FAILED");
        const token = randomBytes(32).toString("hex");
        newSession.run(shaToken(token), account.id, Date.now() + 86400000);
        return reply(res, 200, {
          ok: true, accountId: account.id, accessToken: token, expiresInSeconds: 86400
        });
      }
      if (req.method === "GET" && path === "/api/v1/auth/me") {
        const { account } = auth(req);
        return reply(res, 200, { id: account.id, username: account.username });
      }
      if (req.method === "POST" && path === "/api/v1/auth/logout") {
        const { token } = auth(req);
        removeSession.run(shaToken(token));
        return reply(res, 200, { ok: true });
      }
      return reply(res, 404, { error: "NOT_FOUND" });
    } catch (e) {
      if (!e.status) console.error(e);
      reply(res, e.status || 500, { error: e.status ? e.message : "INTERNAL_SERVER_ERROR" });
    }
  });
  return { server, db };
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const { server } = createApp({ dbPath: process.env.DB_PATH || "./slayer-auth.sqlite" });
  const host = process.env.HOST || "127.0.0.1";
  const port = Number(process.env.PORT || 8787);
  server.listen(port, host, () => console.log("Auth server " + host + ":" + port));
}
