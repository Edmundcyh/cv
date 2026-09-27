# edmundcyh.com

Personal landing page for Edmund Chong, served by **GitHub Pages** at <https://www.edmundcyh.com> with DNS on **Cloudflare (free plan)**.

It is a single static page. A GitHub Actions workflow adds the latest supply chain headlines to it every morning and publishes it:

| File | Purpose |
| --- | --- |
| `index.html` | The landing page (HTML and inline CSS) |
| `404.html` | Page shown by GitHub Pages for unknown URLs |
| `favicon.svg` | Browser tab icon |
| `images/edmundchong.jpg` | Profile photo, also used for link previews |
| `CNAME` | Records the custom domain (`www.edmundcyh.com`); with Actions deploys, the Pages setting below is what counts |
| `news/build.py` | Fetches the news feeds and fills in the news section of the page |
| `news/picks.json` | Your weekly picks, shown above the headlines |
| `.github/workflows/deploy.yml` | Builds and publishes the site on every push to `main` and daily at 06:17 Kuala Lumpur time |

To edit the site, change `index.html` and push to `main`. The workflow redeploys within a minute or two.

## News section

The **News** section has two parts:

- **Headlines** refresh automatically every morning from the feeds listed in `FEEDS` at the top of `news/build.py`: Google News (supply chain news mentioning Malaysia or ASEAN), Supply Chain Dive, The Loadstar, FreightWaves and Splash247. The newest 9 headlines from the last 14 days are shown, with at most 2–3 from any one source. Only the headline, source, date and link are shown, never the article text. If a feed fails it is skipped; if they all fail, the page shows plain links to the publishers instead.
- **My picks** are the stories you choose, with your own comment. This is the part that gives people a reason to come back. To update it, edit `news/picks.json` (on github.com: open the file and click the pencil icon) and commit to `main`:

  ```json
  {
    "week_of": "2026-09-22",
    "picks": [
      {
        "title": "Headline of the article",
        "url": "https://www.example.com/article",
        "source": "The Loadstar",
        "note": "One or two lines on why it matters for retailers in Malaysia."
      }
    ]
  }
  ```

  `source` and `note` are optional. The picks box is hidden while `picks` is empty, and is hidden automatically once `week_of` is more than 30 days old, so an old week never shows as current.

To refresh the headlines immediately, go to **Actions → Deploy site → Run workflow**.

To preview the built page locally, run `python3 news/build.py index.html _site/index.html` and open `_site/index.html` (copy `images/` and `favicon.svg` into `_site/` for the photo and icon).

**Keep the daily refresh running:** GitHub pauses scheduled workflows in public repos after 60 days without a commit. Updating `news/picks.json` counts. If it does get paused, GitHub emails you, and you can turn it back on under **Actions → Deploy site → Enable workflow**.

## Hosting setup

> **Keep this repository public.** On GitHub's free plan, making the repository private switches off GitHub Pages, and www.edmundcyh.com goes down. The daily deploy then fails with "Get Pages site failed … Not Found". To recover, make the repository public (Settings → General → Danger Zone → Change visibility). Then set up the Pages settings below again, including re-entering the custom domain. Finally, go to **Actions**, click **Deploy site** in the list on the left, and use **Run workflow**.

### GitHub (repo → Settings → Pages)

- **Source:** GitHub Actions (the `Deploy site` workflow builds and publishes the page)
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
- **Caching:** the defaults are fine. After an update, *Caching → Purge Everything* makes the change appear immediately.
