import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import hashlib
import time
import random

BASE_URL = "https://www.trendmicro.com"
INDEX_URL = f"{BASE_URL}/vinfo/us/threat-encyclopedia/vulnerability/deep-security-center"
RSS_FILE = "deep_security_updates.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SecurityResearchBot/1.0)"
}

# -------------------------------------------------------------------

def get_latest_rule_update():
    r = requests.get(INDEX_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    link = soup.find("a", string=lambda x: x and "Read more" in x)
    if not link:
        raise RuntimeError("Could not find Rule Update link")

    title_tag = link.find_previous("h2")
    title = title_tag.get_text(strip=True) if title_tag else "Deep Security Rule Update"

    href = link["href"]
    if not href.startswith("http"):
        href = BASE_URL + href

    return title, href

# -------------------------------------------------------------------

def extract_update_content(url):
    time.sleep(random.uniform(2, 4))

    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # fjern støj
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    container = soup.find("main") or soup.body
    if not container:
        raise RuntimeError("No readable content found")

    stop_phrases = [
        "Featured Stories",
        "See all Security Updates"
    ]

    noise = {
        "Email", "Facebook", "Twitter", "Google+", "Linkedin", "Read more"
    }

    lines = []
    for line in container.stripped_strings:
        line = line.strip()

        if any(stop in line for stop in stop_phrases):
            break
        if line in noise:
            continue
        if len(line) < 2:
            continue

        lines.append(line)

    # ---- HTML OPBYGNING ----
    html_parts = []
    for l in lines:
        # sektionstitler
        if l.endswith("Rules:") or l.isupper():
            html_parts.append(f"<h3>{l}</h3>")
        else:
            html_parts.append(f"{l}<br>")

    return "\n".join(html_parts)

# -------------------------------------------------------------------

def generate_rss(title, link, html_content):
    fg = FeedGenerator()
    fg.id(INDEX_URL)
    fg.title("Trend Micro – Deep Security Rule Updates")
    fg.link(href=INDEX_URL, rel="alternate")

    # 🔑 VALIDERINGS-FIX
    fg.link(
        href="https://m1kl0s.github.io/deep-security-dsru-feed/deep_security_updates.xml",
        rel="self",
        type="application/rss+xml"
    )

    fg.subtitle("Unofficial RSS feed for Trend Micro Deep Security Rule Updates")
    fg.language("en")
    fg.lastBuildDate(datetime.now(timezone.utc))

    fe = fg.add_entry()
    fe.id(hashlib.sha256(link.encode()).hexdigest())
    fe.title(title)
    fe.link(href=link)
    fe.published(datetime.now(timezone.utc))

    fe.description(
        "Latest Trend Micro Deep Security Rule Update. See full details in content."
    )
    fe.content(html_content, type="CDATA")

    fg.rss_file(RSS_FILE)

# -------------------------------------------------------------------

if __name__ == "__main__":
    title, link = get_latest_rule_update()
    content = extract_update_content(link)
    generate_rss(title, link, content)
