"""Fill the news section of index.html with fresh headlines and weekly picks.

Usage: python3 news/build.py index.html _site/index.html

Reads the RSS/Atom feeds in FEEDS and the picks in news/picks.json, and
writes a copy of the page with both filled in. Uses only the standard
library, so the GitHub Actions runner needs nothing installed.

A feed that fails is skipped. If every feed fails, the page keeps the
fallback links that are already between the news markers, so a bad day
for the publishers never breaks the site.
"""

import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin

# To change the sources, edit this list. "limit" caps how many headlines
# one source can contribute, so a busy feed doesn't crowd out the rest.
FEEDS = [
    {
        "name": "Google News",
        "url": "https://news.google.com/rss/search?q=%22supply+chain%22+(Malaysia+OR+ASEAN)&hl=en-MY&gl=MY&ceid=MY:en",
        "limit": 3,
    },
    {"name": "Supply Chain Dive", "url": "https://www.supplychaindive.com/feeds/news/", "limit": 2},
    {"name": "The Loadstar", "url": "https://theloadstar.com/feed/", "limit": 2},
    {"name": "FreightWaves", "url": "https://www.freightwaves.com/news/feed", "limit": 2},
    {"name": "Splash247", "url": "https://splash247.com/feed/", "limit": 2},
]

MAX_HEADLINES = 9          # fills a 3 x 3 grid on desktop
MAX_AGE = timedelta(days=14)
MAX_AHEAD = timedelta(hours=1)  # allows for a publisher's clock running fast; later dates are bad data
PICKS_MAX_AGE = timedelta(days=30)  # older picks are hidden rather than shown as "this week"
PICKS_FILE = Path(__file__).with_name("picks.json")
MYT = timezone(timedelta(hours=8))
USER_AGENT = "Mozilla/5.0 (compatible; edmundcyh.com news builder; +https://www.edmundcyh.com/)"

ATOM = "{http://www.w3.org/2005/Atom}"
XML_BASE = "{http://www.w3.org/XML/1998/namespace}base"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read(), resp.url  # after redirects, relative links resolve against the final URL


def clean_text(value):
    """Plain text from a feed field: no tags, entities decoded, spaces collapsed."""
    value = re.sub(r"<[^>]+>", "", value or "")
    value = html.unescape(html.unescape(value))  # some feeds double-encode
    return " ".join(value.split())


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)  # RSS: "Wed, 24 Sep 2026 10:00:00 +0000"
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value)  # Atom: "2026-09-24T10:00:00Z"
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def safe_url(value):
    value = (value or "").strip()
    return value if re.match(r"https?://", value, re.I) else None


def resolve_base(el, parents, url):
    """url resolved through the xml:base of el and each of its ancestors, outermost first."""
    chain = []
    while el is not None:
        chain.append(el)
        el = parents.get(el)
    for el in reversed(chain):
        try:
            url = urljoin(url, el.get(XML_BASE, ""))
        except ValueError:  # a malformed xml:base is ignored, so absolute links still work
            pass
    return url


def atom_link(entry, parents, feed_url):
    """The article URL of an Atom entry, or None.

    Links marked rel="alternate" are tried first, then links with no rel, which
    also mean alternate; "self", "edit", "enclosure" and the like are skipped.
    Relative links are resolved against any xml:base, then the feed's own URL.
    parents maps each element of the document to its parent.
    """
    links = entry.findall(ATOM + "link")
    explicit = [l for l in links if l.get("rel") in ("alternate", "http://www.iana.org/assignments/relation/alternate")]
    for link in explicit + [l for l in links if l.get("rel") is None]:
        href = (link.get("href") or "").strip()
        if not href:
            continue
        try:
            url = safe_url(urljoin(resolve_base(link, parents, feed_url), href))
        except ValueError:  # malformed URL, e.g. an unclosed IPv6 bracket
            continue
        if url:
            return url
    return None


def parse_feed(data, feed):
    root = ET.fromstring(data)
    items = []
    for item in root.iter("item"):  # RSS 2.0
        title = clean_text(item.findtext("title"))
        source = feed["name"]
        publisher = item.find("source")
        if publisher is not None and publisher.text:
            # Google News names the real publisher and appends it to the title.
            source = clean_text(publisher.text)
            suffix = " - " + source
            if title.endswith(suffix):
                title = title[: -len(suffix)]
        items.append({
            "title": title,
            "url": safe_url(item.findtext("link")),
            "date": parse_date(item.findtext("pubDate")),
            "source": source,
        })
    parents = {child: parent for parent in root.iter() for child in parent}
    for entry in root.iter(ATOM + "entry"):  # Atom
        items.append({
            "title": clean_text(entry.findtext(ATOM + "title")),
            "url": atom_link(entry, parents, feed["url"]),
            "date": parse_date(entry.findtext(ATOM + "published") or entry.findtext(ATOM + "updated")),
            "source": feed["name"],
        })
    return items


def collect_headlines(now):
    headlines, seen = [], set()
    for feed in FEEDS:
        try:
            data, final_url = fetch(feed["url"])
            items = parse_feed(data, {**feed, "url": final_url})
        except Exception as exc:  # network error, HTTP error, bad XML
            print(f"skip {feed['name']}: {exc}", file=sys.stderr)
            continue
        # Future dates would sort to the top and stay there; far-future ones crash the rendering.
        fresh = [i for i in items if i["title"] and i["url"] and i["date"] and now - MAX_AGE <= i["date"] <= now + MAX_AHEAD]
        fresh.sort(key=lambda i: i["date"], reverse=True)
        taken = 0
        for item in fresh:
            key = re.sub(r"\W+", "", item["title"].lower())
            if key in seen:
                continue
            seen.add(key)
            headlines.append(item)
            taken += 1
            if taken == feed["limit"]:
                break
        print(f"{feed['name']}: {len(items)} items, {taken} used", file=sys.stderr)
    headlines.sort(key=lambda i: i["date"], reverse=True)
    return headlines[:MAX_HEADLINES]


def load_picks(today):
    data = json.loads(PICKS_FILE.read_text(encoding="utf-8"))
    picks = [p for p in data.get("picks", []) if p.get("title") and safe_url(p.get("url"))]
    if not picks:
        return None, []
    week_of = datetime.strptime(data["week_of"], "%Y-%m-%d").date()
    if today - week_of > PICKS_MAX_AGE:
        print(f"picks for week of {week_of} are over {PICKS_MAX_AGE.days} days old, hiding them", file=sys.stderr)
        return None, []
    return week_of, picks


def day_month(d):
    return f"{d.day} {d:%b}"


def render_headlines(headlines, now):
    esc = html.escape
    cards = "\n".join(
        f'          <li><a href="{esc(h["url"])}" target="_blank" rel="noopener">'
        f'<span class="meta">{esc(h["source"])} · {day_month(h["date"].astimezone(MYT))}</span>'
        f'<span class="title">{esc(h["title"])}</span></a></li>'
        for h in headlines
    )
    local = now.astimezone(MYT)
    return (
        '\n        <ul class="headlines">\n'
        f"{cards}\n"
        "        </ul>\n"
        f'        <p class="news-note">Updated {day_month(local)} {local.year}. Headlines link to the original publishers.</p>\n        '
    )


def render_picks(week_of, picks):
    esc = html.escape
    items = []
    for p in picks:
        source = f'<span class="meta">{esc(p["source"])}</span>' if p.get("source") else ""
        note = f'<p>{esc(p["note"])}</p>' if p.get("note") else ""
        items.append(
            f'            <li>{source}<a href="{esc(p["url"])}" target="_blank" rel="noopener">{esc(p["title"])}</a>{note}</li>'
        )
    return (
        '\n        <div class="picks">\n'
        f'          <h3>My picks <span>Week of {day_month(week_of)} {week_of.year}</span></h3>\n'
        '          <ol>\n'
        + "\n".join(items) + "\n"
        '          </ol>\n'
        '        </div>\n        '
    )


def replace_between(page, name, content):
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    if page.count(start) != 1 or page.count(end) != 1:
        sys.exit(f"index.html must contain exactly one {start} and one {end}")
    head, rest = page.split(start)
    _, tail = rest.split(end)
    return head + start + content + end + tail


def main(src, dest):
    now = datetime.now(timezone.utc)
    page = Path(src).read_text(encoding="utf-8")

    week_of, picks = load_picks(now.astimezone(MYT).date())
    page = replace_between(page, "picks", render_picks(week_of, picks) if picks else "")

    headlines = collect_headlines(now)
    if headlines:
        page = replace_between(page, "news", render_headlines(headlines, now))
    else:
        print("no headlines fetched, keeping the fallback links", file=sys.stderr)

    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    Path(dest).write_text(page, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
