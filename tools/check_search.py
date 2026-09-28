"""Validate the generated site's search discovery files: python tools/check_search.py."""
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import OUT, SITE_URL


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.canonicals = []
        self.description = ""
        self.robots = ""
        self.title = ""
        self.in_title = False
        self.h1_count = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href", ""))
        if tag == "meta":
            if attrs.get("name") == "description":
                self.description = attrs.get("content", "")
            if attrs.get("name") == "robots":
                self.robots = attrs.get("content", "").lower()
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1_count += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, text):
        if self.in_title:
            self.title += text


def check():
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap = ET.parse(OUT / "sitemap.xml").getroot()
    assert sitemap.tag == "{" + ns["s"] + "}urlset", "Invalid sitemap namespace"
    urls = [node.text for node in sitemap.findall("s:url/s:loc", ns)]
    assert urls and len(urls) == len(set(urls)), "Empty sitemap or duplicate URLs"
    robots = RobotFileParser()
    robots.parse((OUT / "robots.txt").read_text(encoding="utf-8").splitlines())
    assert robots.site_maps() == [SITE_URL + "/sitemap.xml"], "Incorrect sitemap directive"
    expected = set()
    titles = set()
    for path in OUT.rglob("*.html"):
        rel = path.relative_to(OUT).as_posix()
        url = (SITE_URL + "/" + rel).replace("/index.html", "/")
        page = Page(path.read_text(encoding="utf-8"))
        assert len(page.canonicals) == 1, f"Expected one canonical: {rel}"
        canonical = page.canonicals[0]
        assert canonical.startswith(SITE_URL + "/"), f"Canonical uses wrong domain: {rel}"
        parts = urlsplit(canonical)
        assert not parts.query and not parts.fragment, f"Noncanonical query/fragment: {rel}"
        target = OUT / parts.path.lstrip("/")
        if target.is_dir():
            target /= "index.html"
        assert target.is_file(), f"Canonical target missing: {rel}"
        assert page.title.strip() and page.description.strip(), f"Missing title/description: {rel}"
        assert page.h1_count == 1, f"Expected one main heading: {rel}"
        if rel == "404.html" or rel.startswith("_"):
            assert "noindex" in page.robots, f"Error/private page is indexable: {rel}"
        if "noindex" not in page.robots and canonical == url:
            expected.add(url)
            assert page.title not in titles, f"Duplicate title: {rel}"
            titles.add(page.title)
    assert set(urls) == expected, f"Sitemap mismatch: {set(urls) ^ expected}"
    agents = ["Googlebot", "Bingbot", "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot"]
    for agent in agents:
        for url in urls + [SITE_URL + "/css/site.css", SITE_URL + "/js/site.js"]:
            assert robots.can_fetch(agent, url), f"Blocked crawler: {agent} {url}"
    print(f"PASS: {len(urls)} canonical sitemap URLs; metadata, exclusions, robots.txt and {len(agents)} search crawler policies.")
    print("Local build only. Deployment responses, firewall rules and actual indexing require live verification.")


if __name__ == "__main__":
    check()
