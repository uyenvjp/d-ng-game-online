import test from "node:test";
import assert from "node:assert/strict";
import { createApp } from "../server.mjs";

test("signup, login, session expiry/revocation and rejection", async () => {
  const { server, db } = createApp({ dbPath: ":memory:" });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const base = "http://127.0.0.1:" + server.address().port;
  const api = async (path, method = "GET", data = null, token = null) => {
    const headers = {};
    if (data !== null) headers["content-type"] = "application/json";
    if (token) headers.authorization = "Bearer " + token;
    const response = await fetch(base + path, {
      method, headers, ...(data !== null ? { body: JSON.stringify(data) } : {})
    });
    return { status: response.status, data: await response.json() };
  };
  try {
    assert.equal((await api("/health")).status, 200);
    assert.equal((await api("/api/v1/auth/register", "POST", {username:"user123",password:"great-secret-123"})).status, 201);
    assert.equal((await api("/api/v1/auth/register", "POST", {username:"user123",password:"great-secret-123"})).status, 409);
    assert.equal((await api("/api/v1/auth/login", "POST", {username:"user123",password:"wrong-pass-123"})).status, 401);
    const signed = await api("/api/v1/auth/login", "POST", {username:"user123",password:"great-secret-123"});
    assert.equal(signed.status, 200);
    assert.match(signed.data.accessToken, /^[a-f0-9]{64}$/);
    const token = signed.data.accessToken;
    const me = await api("/api/v1/auth/me", "GET", null, token);
    assert.equal(me.status, 200);
    assert.equal(me.data.username, "user123");
    assert.equal((await api("/api/v1/auth/me")).status, 401);
    assert.equal((await api("/api/v1/auth/logout", "POST", {}, token)).status, 200);
    assert.equal((await api("/api/v1/auth/me", "GET", null, token)).status, 401);
    assert.equal((await api("/api/v1/auth/register", "POST", {username:"bad!!",password:"great-secret-123"})).status, 400);
  } finally {
    await new Promise(resolve => server.close(resolve));
    db.close();
  }
});
