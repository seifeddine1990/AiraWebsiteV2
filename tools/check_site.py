"""Check generated local links, assets and basic HTML semantics after build.py."""
from collections import Counter
import hashlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "public"


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.refs, self.labels, self.fields, self.issues = [], [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        for name in ("href", "src"):
            if name in attrs:
                self.refs.append(attrs[name])
        if tag == "img" and "alt" not in attrs:
            self.issues.append("Image has no alt attribute")
        if tag == "label":
            self.labels.append(attrs.get("for"))
        if tag in ("input", "select", "textarea") and attrs.get("type") != "hidden":
            self.fields.append(attrs)


def check():
    pages = {p.resolve(): Page(p.read_text(encoding="utf-8")) for p in ROOT.rglob("*.html")}
    assert pages, "Build the site first"
    issues, count = [], 0
    for path, page in pages.items():
        errors = list(page.issues)
        errors.extend(f"Duplicate ID: {key}" for key, n in Counter(page.ids).items() if n > 1)
        for field in page.fields:
            if not (field.get("id") in page.labels or field.get("aria-label") or field.get("aria-labelledby")):
                errors.append(f"Unlabelled field: {field.get('name')}")
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            count += 1
            target = ((ROOT / unquote(url.path).lstrip("/")) if url.path.startswith("/") else (path.parent / unquote(url.path))) if url.path else path
            target = target.resolve()
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                errors.append(f"Missing reference: {ref}")
                continue
            if url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f"Missing anchor: {ref}")
            if target.suffix in (".css", ".js"):
                expected = hashlib.sha256(target.read_bytes()).hexdigest()[:12]
                if parse_qs(url.query).get("v") != [expected]:
                    errors.append(f"Missing or stale asset version: {ref}")
        issues.extend(f"{path.relative_to(ROOT)}: {error}" for error in errors)
    assert not issues, "\n".join(issues)
    print(f"PASS: {len(pages)} pages, {count} local references, unique IDs, image alt attributes, field labels and asset versions")


if __name__ == "__main__":
    check()
