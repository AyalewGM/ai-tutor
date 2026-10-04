# Cloudflare Edge Security Setup

> **Scope:** Putting Mihur behind Cloudflare's free plan — DNS/proxying,
> origin lockdown, country restriction, Turnstile bot checks, and edge rate
> limiting — plus the app settings that trust Cloudflare's headers.
>
> **Read this fully before enabling `GEO_ENFORCEMENT_ENABLED`.** Turning on
> enforcement before Cloudflare fronts the app fails closed and blocks
> everyone, including you.

---

## 1. What Cloudflare does vs. what the app does

| Control | Layer | Notes |
|---------|-------|-------|
| DDoS absorption, TLS, CDN | Cloudflare (automatic on the free plan) | |
| Country blocking at the edge | Cloudflare WAF rule (optional but recommended) | Blocks before traffic reaches the VPS |
| Country restriction in-app | `GEO_ENFORCEMENT_ENABLED` + `CF-IPCountry` | Backstop if an edge rule is missing; also enforces the travel exemption |
| Datacenter/hosting-network challenge | Cloudflare WAF rule (optional) | Most attack scripts run from hosting providers |
| Bot check on sign-in/sign-up | Cloudflare Turnstile + `TURNSTILE_*` | Invisible challenge, verified server-side |
| Sign-in/registration rate limits | App (`AUTH_THROTTLES_*`) + optional Cloudflare rate-limit rule | App limits are the authoritative layer |
| Failed-sign-in account lockout | App (`LOGIN_MAX_FAILED_ATTEMPTS`) | |
| Firewall for everything else | Cloudflare free WAF + Mihur's own auth checks | |

## 2. Step 1 — Put the domain on Cloudflare (free plan)

1. Create a Cloudflare account at cloudflare.com and **Add a site** → enter the
   Mihur domain → choose the **Free** plan.
2. Cloudflare lists the DNS records it found. Confirm there is an **A record**
   for the domain pointing at the VPS IP, with the **proxy status = orange
   cloud (Proxied)**. That is what routes traffic through Cloudflare.
3. At the domain registrar, change the nameservers to the two Cloudflare
   gives you. Wait until Cloudflare says the site is **Active**.
4. **SSL/TLS → Overview:** set encryption mode to **Full (strict)**. If the
   origin doesn't have its own certificate yet, **SSL/TLS → Origin Server →
   Create Certificate** gives you a free origin cert Cloudflare will trust.

Until the nameserver change is active, nothing below works — the `CF-*`
headers only exist on traffic Cloudflare proxies.

## 3. Step 2 — Lock the origin so only Cloudflare can reach it

If an attacker finds the VPS IP directly, every Cloudflare rule is bypassed —
including the geo headers, which they'd be free to fake. Pick one:

**Recommended: Cloudflare Tunnel (`cloudflared`).** No open inbound ports at
all; outbound-only connection from the VPS to Cloudflare.
Cloudflare Zero Trust → Networks → Tunnels → create → run the shown
`cloudflared` install on the VPS → point the tunnel's public hostname at
`http://localhost:3000`. Then close the public port (`ufw deny 3000` etc.).

**Alternative: firewall allowlist.** Only allow inbound HTTP(S) from
Cloudflare's published IP ranges (cloudflare.com/ips — they change rarely but
do change, so the tunnel option is lower maintenance).

## 4. Step 3 — Turn on the app's trust + enforcement

Only after steps 1–2 are live, set in `.env.pilot`:

```env
CLOUDFLARE_TRUSTED=true        # app may trust CF-IPCountry / CF-Connecting-IP
GEO_ENFORCEMENT_ENABLED=true   # block anything not in ALLOWED_COUNTRIES
ALLOWED_COUNTRIES=US,CA
```

`docker compose -f docker-compose.yml -f docker-compose.pilot.yml up -d` to
apply.

**Behavior once enabled:**
- Requests with `CF-IPCountry` of `US` or `CA` → normal.
- Any other country → `403 REGION_NOT_SUPPORTED`; the SPA shows the
  "Not available in your region" page. **Exception:** requests carrying a
  valid session for an *approved* family (or a staff account) are allowed —
  families travel.
- Missing header, `XX` (unknown) or `T1` (Tor) → blocked for everyone.
- Sign-up (`/auth/register-parent`) is *never* reachable from a non-US/CA
  country, session or not.
- `/api/v1/auth/login`, `/api/v1/auth/config`,
  `/api/v1/practice-pass/activate` (learner sign-in), `/health`, `/ready`
  stay reachable worldwide so approved families can re-authenticate while
  travelling; sign-in is protected by the throttle/lockout/Turnstile layers.
- Every block is logged (`geo block: path=… country=…`). IP addresses are
  not logged.

## 5. Step 4 — Optional: edge WAF rules (block before the VPS)

Cloudflare Dashboard → Security → WAF → Custom rules:

1. **Country block.** Field `Country` *is not in* `United States`, `Canada` →
   **Block** (or **Managed Challenge** to be gentler). Keep `/api/v1/auth/*`
   out of this rule if you want sign-in to stay reachable for travelling
   families — or let the app handle it and skip this rule entirely.
2. **Hosting-network challenge (anti-VPN/anti-script).** Field
   `IP source address` `is in` — simpler alternative: `Verified Bot` etc. For
   free plans, a practical rule is **Managed Challenge** when
   `cf.threat_score` is high, or challenge traffic from hosting ASNs
   (e.g., AS14061 DigitalOcean, AS16509/AS14618 Amazon, AS15169 Google,
   AS8075 Microsoft — verify each ASN before adding).
3. **Rate limit** (free plan allows one rule): `/api/v1/auth/*`, more than
   ~20 requests per minute per IP → Block for 10 minutes. Backstop to the
   app's own throttles.

## 6. Step 5 — Turnstile bot check

1. Cloudflare Dashboard → **Turnstile → Add site** → domain →
   **Widget mode: Managed** (invisible for most users) → create.
2. Copy the **Site Key** and **Secret Key** into `.env.pilot`:

   ```env
   TURNSTILE_SITE_KEY=0x4AAAAA...
   TURNSTILE_SECRET_KEY=0x4AAAAA...
   ```

3. Restart the stack. The sign-in/registration page fetches
   `/api/v1/auth/config`, renders the widget, and the API verifies each token
   against `siteverify` before checking credentials.

When the secret is set, missing/invalid/expired tokens are rejected
(`400`), and an unreachable Cloudflare denies the attempt (`503`) — fail
closed. Tokens are never logged or stored. To disable: blank
`TURNSTILE_SECRET_KEY` (the widget disappears automatically).

## 7. App throttles and lockout

| Setting | Default | Meaning |
|---------|---------|---------|
| `LOGIN_RATE_LIMIT_PER_IP` / `_WINDOW_SECONDS` | 20 / 900 | Sign-in attempts per IP per window → `429` |
| `REGISTER_RATE_LIMIT_PER_IP` / `_WINDOW_SECONDS` | 5 / 3600 | Registrations per IP per window → `429` |
| `LOGIN_MAX_FAILED_ATTEMPTS` / `LOGIN_LOCKOUT_SECONDS` | 5 / 900 | Failed passwords per account → `429` until the window expires. Success clears the counter. |
| `AUTH_THROTTLES_ENABLED` | `true` | Tests/dev only — keep on in production. |

Counters live in Redis (`rl:*` keys; emails are SHA-256'd). If Redis is down
the endpoints answer `503` rather than allow unlimited guessing — same
fail-closed behavior as admin MFA.

## 8. Local development & CI

Defaults are safe by omission: `CLOUDFLARE_TRUSTED=false`,
`GEO_ENFORCEMENT_ENABLED=false`, Turnstile keys empty, throttles on with
generous dev limits in `docker-compose.yml`. Nothing to do locally — the
geo and Turnstile code paths are covered by the test suite via settings
overrides.

## 9. Go-live checklist

- [ ] Domain active on Cloudflare, A record proxied (orange cloud)
- [ ] SSL/TLS = Full (strict)
- [ ] Origin locked down (tunnel or IP allowlist)
- [ ] Origin lockdown verified: `curl --resolve domain:443:VPS_IP https://domain`
      (or direct `curl http://VPS_IP:3000`) must fail to connect — otherwise a
      spoofed `CF-IPCountry: US` header sent straight to the VPS opens the gate
- [ ] `GEO_ENFORCEMENT_ENABLED=true` → US/CA work, other/unknown 403
- [ ] Turnstile keys set → widget renders on /login
- [ ] `AUTH_THROTTLES_ENABLED=true`, real limit values
- [ ] Optional WAF rules (country, ASN challenge, auth rate limit)
