// Mochi Pomodoro API (Cloudflare Worker)
//
// GET /session -> { t, s, wait }  signed timestamp + how long the page should wait
// GET /tip?t=&s= -> { text }       only if the signature is valid AND `wait` ms have passed
//
// Secrets (never in this repo):  MESSAGE, SIGNING_KEY
// Variable (wrangler.toml):      DELAY_MS

const enc = new TextEncoder();

const b64url = buf => btoa(String.fromCharCode(...new Uint8Array(buf)))
  .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

const fromB64url = str => {
  const b = atob(str.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(b, c => c.charCodeAt(0));
};

const hmacKey = secret => crypto.subtle.importKey(
  "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
  },
});

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const wait = Number(env.DELAY_MS) || 20000;
    if (!env.SIGNING_KEY || !env.MESSAGE) return json({ error: "not configured" }, 500);
    const key = await hmacKey(env.SIGNING_KEY);

    if (url.pathname === "/session") {
      const t = String(Date.now());
      const s = b64url(await crypto.subtle.sign("HMAC", key, enc.encode(t)));
      return json({ t, s, wait });
    }

    if (url.pathname === "/tip") {
      const t = url.searchParams.get("t") || "";
      const s = url.searchParams.get("s") || "";
      let valid = false;
      try {
        valid = /^\d{13}$/.test(t) && await crypto.subtle.verify("HMAC", key, fromB64url(s), enc.encode(t));
      } catch { valid = false; }
      if (!valid) return json({ error: "invalid" }, 403);
      if (Date.now() - Number(t) < wait) return json({ error: "too early" }, 425);
      return json({ text: env.MESSAGE });
    }

    return json({ error: "not found" }, 404);
  },
};
