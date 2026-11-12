#!/usr/bin/env python3
"""Fetch public tax/finance news and write static JSON for the site.

Only public pages are requested. When a source is unavailable, the source
status is recorded as an error instead of replacing it with invented content.
"""

import html
import json
import re
import ssl
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "site" / "data"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
}
SSL_CONTEXT = ssl.create_default_context()
SHANGHAI = timezone(timedelta(hours=8))

ANCHOR_RE = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
TITLE_ATTR_RE = re.compile(r"\btitle=[\"']([^\"']*)[\"']", re.I | re.S)
DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")
URL_DATE_RE = re.compile(r"/(20\d{6})/")


def fetch(url, timeout=25):
    """Return (status_code, text, error_message)."""
    last_error = ""
    for attempt in range(2):
        try:
            request = Request(url, headers=HEADERS)
            with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
                raw = response.read()
                charset = (response.headers.get_content_charset() or "utf-8").lower()
                if charset in ("gb2312", "gbk"):
                    charset = "gb18030"
                try:
                    text = raw.decode(charset, errors="replace")
                except LookupError:
                    text = raw.decode("utf-8", errors="replace")
                return response.status, text, ""
        except HTTPError as error:
            return error.code, "", "HTTP {}".format(error.code)
        except URLError as error:
            last_error = "网络错误：{}".format(str(error.reason)[:120])
        except Exception as error:
            last_error = "{}：{}".format(type(error).__name__, str(error)[:120])
        if attempt == 0:
            time.sleep(0.8)
    return 0, "", last_error or "未知网络错误"


def clean_text(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def anchors(page):
    """Yield (href, title, anchor_start, anchor_end)."""
    for match in ANCHOR_RE.finditer(page):
        href = html.unescape(match.group(1)).strip()
        tag = match.group(0)
        title_match = TITLE_ATTR_RE.search(tag)
        title = clean_text(title_match.group(1) if title_match else match.group(2))
        if href and title:
            yield href, title, match.start(), match.end()


def date_from_url(url):
    match = URL_DATE_RE.search(url)
    if not match:
        return ""
    try:
        value = datetime.strptime(match.group(1), "%Y%m%d")
        return value.strftime("%Y-%m-%d")
    except ValueError:
        return ""


def article_date(url):
    status, page, _ = fetch(url, timeout=20)
    if status != 200:
        return ""
    match = re.search(r"<meta[^>]+name=[\"']PubDate[\"'][^>]+content=[\"']([^\"']+)", page, re.I)
    if not match:
        match = re.search(r"<PUBLISHTIME>([^<]+)</PUBLISHTIME>", page, re.I)
    if not match:
        match = DATE_RE.search(page[:12000])
    if not match:
        return ""
    value = match.group(1) if match.groups() else match.group(0)
    date_match = DATE_RE.search(value)
    return date_match.group(0) if date_match else ""


def record(name, url, status, message, count=0):
    return {
        "name": name,
        "url": url,
        "status": status,
        "message": message,
        "count": count,
    }


def extract_tax():
    url = "https://www.chinatax.gov.cn/chinatax/index.html"
    status, page, error = fetch(url)
    if status != 200:
        message = "HTTP 403（站点反爬或访问限制）" if status == 403 else (error or "页面不可用")
        return [], record("国家税务总局", url, "error", message)

    items = []
    seen = set()
    for href, title, _, _ in anchors(page):
        if "/chinatax/" not in href or not href.rstrip("/").endswith("content.html"):
            continue
        absolute = urljoin(url, href)
        if absolute in seen or len(title) < 8:
            continue
        seen.add(absolute)
        items.append({
            "title": title,
            "url": absolute,
            "source": "国家税务总局",
            "category": "domestic",
            "published_at": "",
            "summary": "国家税务总局公开发布，点击查看原文。",
        })
        if len(items) >= 6:
            break

    for item in items:
        item["published_at"] = article_date(item["url"])

    if not items:
        return [], record("国家税务总局", url, "warn", "页面可访问，但未解析到新闻条目。")
    return items, record("国家税务总局", url, "ok", "公开页面抓取正常。", len(items))


def extract_xinhua():
    url = "https://www.news.cn/fortune/index.htm"
    status, page, error = fetch(url)
    if status != 200:
        message = "HTTP 403（站点反爬或访问限制）" if status == 403 else (error or "页面不可用")
        return [], record("新华财经", url, "error", message)

    items = []
    seen = set()
    for href, title, _, _ in anchors(page):
        absolute = urljoin(url, href)
        if not re.search(r"/fortune/20\d{6}/[0-9a-f]+/c\.html$", absolute):
            continue
        if absolute in seen or len(title) < 8:
            continue
        seen.add(absolute)
        items.append({
            "title": title,
            "url": absolute,
            "source": "新华财经",
            "category": "finance",
            "published_at": date_from_url(absolute),
            "summary": "新华财经公开报道，详情以原文为准。",
        })
        if len(items) >= 9:
            break

    if not items:
        return [], record("新华财经", url, "warn", "页面可访问，但未解析到新闻条目。")
    return items, record("新华财经", url, "ok", "公开页面抓取正常。", len(items))


def extract_pbc():
    url = "https://www.pbc.gov.cn/goutongjiaoliu/113456/index.html"
    status, page, error = fetch(url)
    if status != 200:
        message = "HTTP 403（站点反爬或访问限制）" if status == 403 else (error or "页面不可用")
        return [], record("中国人民银行", url, "error", message)

    items = []
    seen = set()
    for href, title, _, end in anchors(page):
        absolute = urljoin(url, href)
        if not re.search(r"/goutongjiaoliu/113456/\d+/20\d{10,}/index\.html$", absolute):
            continue
        if absolute in seen or len(title) < 8:
            continue
        seen.add(absolute)
        nearby = page[end:end + 800]
        date_match = DATE_RE.search(nearby)
        items.append({
            "title": title,
            "url": absolute,
            "source": "中国人民银行",
            "category": "finance",
            "published_at": date_match.group(0) if date_match else "",
            "summary": "中国人民银行公开发布，详情以原文为准。",
        })
        if len(items) >= 8:
            break

    if not items:
        return [], record("中国人民银行", url, "warn", "页面可访问，但未解析到新闻条目。")
    return items, record("中国人民银行", url, "ok", "公开页面抓取正常。", len(items))


def external_status(name, url):
    status, _, error = fetch(url)
    if status == 200:
        return record(name, url, "warn", "页面可访问，但当前未配置稳定的文章解析规则。")
    if status == 403:
        return record(name, url, "error", "HTTP 403（站点反爬或访问限制）。")
    return record(name, url, "error", error or "页面不可用。")


def build_payload():
    items = []
    sources = []

    for extractor in (extract_tax, extract_xinhua, extract_pbc):
        source_items, source_record = extractor()
        items.extend(source_items)
        sources.append(source_record)

    sources.append(external_status("OECD", "https://www.oecd.org/en/topics/taxation.html"))
    sources.append(external_status("Wolters Kluwer", "https://www.wolterskluwer.com/en/news"))

    deduped = []
    seen_urls = set()
    for item in items:
        if item["url"] in seen_urls:
            continue
        seen_urls.add(item["url"])
        deduped.append(item)

    deduped.sort(key=lambda item: item.get("published_at") or "0000-00-00", reverse=True)

    now = datetime.now(SHANGHAI)
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "generated_at_display": now.strftime("%Y-%m-%d %H:%M"),
        "items": deduped,
        "sources": sources,
    }


def main():
    payload = build_payload()
    if not payload["items"]:
        print("ERROR: no news items were parsed; existing data was left unchanged.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "news.json"
    js_path = OUT_DIR / "news-data.js"
    dumped = json.dumps(payload, ensure_ascii=False, indent=2)
    json_path.write_text(dumped + "\n", encoding="utf-8")
    js_path.write_text("window.NEWS_DATA = " + dumped + ";\n", encoding="utf-8")

    print("Wrote {} items at {}".format(len(payload["items"]), payload["generated_at_display"]))
    for source in payload["sources"]:
        print("- {}: {} ({} items) {}".format(source["name"], source["status"], source["count"], source["message"]))
    return 0


if __name__ == "__main__":

    sys.exit(main())