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

def get_latest_rule_update():
    r = requests.get(INDEX_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Første "Read more" link = seneste Rule Update
    link = soup.find("a", string=lambda x: x and "Read more" in x)
    if not link:
        raise RuntimeError("Could not find Rule Update link")

    title = link.find_previous("h2")
    title_text = title.get_text(strip=True) if title else "Deep Security Rule Update"

    href = link["href"]
    if not href.startswith("http"):
        href = BASE_URL + href

    return title_text, href

def extract_update_content(url):
    time.sleep(random.uniform(2, 4))  # vær flink mod Trend Micro

    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Fjern støj
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    container = soup.find("main") or soup.body
    if not container:
        raise RuntimeError("Could not locate readable content")

    lines = []

    stop_phrases = [
        "Featured Stories",
        "See all Security Updates"
    ]

    noise_phrases = {
        "Email", "Facebook", "Twitter", "Google+",
        "Linkedin", "Read more"
    }

    for line in container.stripped_strings:
        line = line.strip()

        # Stop når marketing starter
        if any(stop in line for stop in stop_phrases):
            break

        # Fjern støj
        if line in noise_phrases:
            continue

        if len(line) < 2:
            lines.append("")  # bevar tom linje
            continue

        lines.append(line)

    # ── FORMATERING ─────────────────────────────
    text = "\n".join(lines)

    # Normalisér whitespace
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    # Konverter til HTML der virker i RSS-readers
    html = (
        "<pre style=\"white-space: pre-wrap; font-family: monospace;\">"
        + text.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace("\n", "<br>")
        + "</pre>"
    )

    return html




def generate_rss(title, link, content):
    fg = FeedGenerator()
    fg.id(INDEX_URL)
    fg.title("Trend Micro – Deep Security Rule Updates")
    fg.link(href=INDEX_URL, rel="alternate")
    fg.subtitle("Official Deep Security Rule Update feed (scraped)")
    fg.language("en")

    fe = fg.add_entry()
    fe.id(hashlib.sha256(link.encode()).hexdigest())
    fe.title(title)
    fe.link(href=link)
    fe.published(datetime.now(timezone.utc))
    fe.description(content)
    fe.content(content, type="CDATA")

    fg.rss_file(RSS_FILE)


if __name__ == "__main__":
    title, link = get_latest_rule_update()
    content = extract_update_content(link)
    generate_rss(title, link, content)
