# edmundcyh.com

Personal landing page for Edmund Chong, served by **GitHub Pages** at <https://www.edmundcyh.com> with DNS on **Cloudflare (free plan)**.

It is a single static page with no build step:

| File | Purpose |
| --- | --- |
| `index.html` | The landing page (HTML and inline CSS) |
| `404.html` | Page shown by GitHub Pages for unknown URLs |
| `favicon.svg` | Browser tab icon |
| `images/edmundchong.jpg` | Profile photo, also used for link previews |
| `CNAME` | Tells GitHub Pages which custom domain to serve (`www.edmundcyh.com`) |

To edit the site, change `index.html` and push to `main`. GitHub Pages redeploys within a minute or two.

## Hosting setup

### GitHub (repo → Settings → Pages)

- **Source:** Deploy from a branch → `main` / `(root)`
- **Custom domain:** `www.edmundcyh.com`
- **Enforce HTTPS:** on (it becomes available after GitHub issues the certificate)

### Cloudflare DNS (edmundcyh.com → DNS → Records)

| Type | Name | Content | Proxy |
| --- | --- | --- | --- |
| CNAME | `www` | `edmundcyh.github.io` | Proxied (orange) |
| A | `@` | `185.199.108.153` | Proxied (orange) |
| A | `@` | `185.199.109.153` | Proxied (orange) |
| A | `@` | `185.199.110.153` | Proxied (orange) |
| A | `@` | `185.199.111.153` | Proxied (orange) |

GitHub redirects the apex (`edmundcyh.com`) to `www.edmundcyh.com` automatically.

**First-time certificate:** if GitHub says the domain is "not properly configured" or HTTPS is unavailable, set these records to **DNS only (grey cloud)** until GitHub shows the certificate as issued. Then switch them back to Proxied.

### Cloudflare settings (all available on the free plan)

- **SSL/TLS → Overview → Encryption mode: Full (strict).** Do not use *Flexible*, because it causes an infinite redirect loop with GitHub's HTTPS enforcement.
- **SSL/TLS → Edge Certificates:** turn on *Always Use HTTPS*.
- **Scrape Shield → Email Address Obfuscation:** on. This hides the email address on the page from spam bots.
- **Caching:** the defaults are fine. After an update, *Caching → Purge Everything* makes the change appear immediately.
