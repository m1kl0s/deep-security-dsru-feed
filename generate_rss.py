import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import hashlib

URL = "https://www.trendmicro.com/vinfo/us/threat-encyclopedia/vulnerability/deep-security-center"
RSS_FILE = "deep_security_vulns.xml"

import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SecurityResearchBot/1.0)"
}

def fetch_entries():
    retries = 5
    backoff = 5  # seconds

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(URL, headers=HEADERS, timeout=30)

            if r.status_code == 429:
                wait = backoff * attempt + random.uniform(1, 3)
                print(f"[!] Rate limited (429). Waiting {wait:.1f}s (attempt {attempt}/{retries})")
                time.sleep(wait)
                continue

            r.raise_for_status()
            break

        except requests.exceptions.RequestException as e:
            if attempt == retries:
                print(f"[!] Failed after {retries} attempts: {e}")
                return []

            wait = backoff * attempt
            print(f"[!] Error: {e}. Retrying in {wait}s")
            time.sleep(wait)

    soup = BeautifulSoup(r.text, "html.parser")
    entries = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]

        if not title or "Deep Security" not in title:
            continue

        if not href.startswith("http"):
            href = "https://www.trendmicro.com" + href

        entries.append({
            "title": title,
            "link": href
        })

    return {e["link"]: e for e in entries}.values()


def generate_rss(entries):
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("Trend Micro – Deep Security Vulnerability Updates")
    fg.link(href=URL, rel="alternate")
    fg.subtitle("Auto-generated RSS feed (GitHub Actions)")
    fg.language("en")

    for entry in entries:
        fe = fg.add_entry()
        fe.id(hashlib.sha256(entry["link"].encode()).hexdigest())
        fe.title(entry["title"])
        fe.link(href=entry["link"])
        fe.published(datetime.utcnow())

    fg.rss_file(RSS_FILE)

if __name__ == "__main__":
    entries = fetch_entries()
    generate_rss(entries)
