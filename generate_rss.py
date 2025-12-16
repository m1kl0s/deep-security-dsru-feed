import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import hashlib

URL = "https://www.trendmicro.com/vinfo/us/threat-encyclopedia/vulnerability/deep-security-center"
RSS_FILE = "deep_security_vulns.xml"

def fetch_entries():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    entries = []

    for a in soup.select("a[href]"):
        title = a.get_text(strip=True)
        href = a.get("href")

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
