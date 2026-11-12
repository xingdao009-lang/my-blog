#!/usr/bin/env python3
"""Build article list data and published HTML pages from reviewed JSON drafts.

Only articles with status "published" are written to the public site. An article
must include sources or material notes and review metadata before it can pass
validation. Draft and review files stay in content/articles and are not served.
"""

import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = BASE_DIR / "content" / "articles"
SITE_DIR = BASE_DIR / "site"
ARTICLES_DIR = SITE_DIR / "articles"
DATA_DIR = SITE_DIR / "data"
SHANGHAI = timezone(timedelta(hours=8))

SECTION_LABELS = {"tax-law": "财税普法", "ai": "AI 赋能"}
SECTION_URLS = {"tax-law": "../tax-law.html", "ai": "../ai.html"}
STATUSES = {"draft", "review", "published"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_articles():
    articles = []
    if not CONTENT_DIR.exists():
        return articles
    for path in sorted(CONTENT_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            articles.append({"__path": str(path), "__load_error": str(error)})
            continue
        data["__path"] = str(path)
        articles.append(data)
    return articles


def inline_format(value):
    text = html.escape(value or "")
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        text,
    )
    return text


def markdown_to_html(markdown):
    lines = (markdown or "").splitlines()
    out = []
    paragraph = []
    list_type = ""
    list_items = []
    code_lines = []
    in_code = False

    def flush_paragraph():
        if paragraph:
            out.append("<p>" + inline_format(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def flush_list():
        nonlocal list_type, list_items
        if list_type == "ul":
            out.append("<ul>" + "".join("<li>" + inline_format(item) + "</li>" for item in list_items) + "</ul>")
        elif list_type == "ol":
            out.append("<ol>" + "".join("<li>" + inline_format(item) + "</li>" for item in list_items) + "</ol>")
        list_type = ""
        list_items = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
            continue
        if in_code:
            code_lines.append(raw_line)
            continue
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = 2 + max(0, len(heading.group(1)) - 2)
            out.append("<h{0}>{1}</h{0}>".format(level, inline_format(heading.group(2))))
            continue
        if line.strip() == "---":
            flush_paragraph()
            flush_list()
            out.append("<hr>")
            continue
        if line.startswith("> "):
            flush_paragraph()
            flush_list()
            out.append("<blockquote>" + inline_format(line[2:]) + "</blockquote>")
            continue
        unordered = re.match(r"^-\s+(.+)$", line)
        if unordered:
            flush_paragraph()
            if list_type != "ul":
                flush_list()
                list_type = "ul"
            list_items.append(unordered.group(1))
            continue
        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered:
            flush_paragraph()
            if list_type != "ol":
                flush_list()
                list_type = "ol"
            list_items.append(ordered.group(1))
            continue
        paragraph.append(line.strip())

    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    flush_paragraph()
    flush_list()
    return "\n".join(out)


def validate_article(article):
    errors = []
    path = article.get("__path", "unknown")
    if article.get("__load_error"):
        return ["{}: JSON 解析失败：{}".format(path, article["__load_error"])]

    slug = str(article.get("slug", "")).strip()
    section = str(article.get("section", "")).strip()
    status = str(article.get("status", "draft")).strip()

    if not SLUG_RE.match(slug):
        errors.append("{}: slug 只能使用小写字母、数字和短横线。".format(path))
    if section not in SECTION_LABELS:
        errors.append("{}: section 必须是 tax-law 或 ai。".format(path))
    if status not in STATUSES:
        errors.append("{}: status 必须是 draft、review 或 published。".format(path))

    if status == "published":
        if not str(article.get("title", "")).strip():
            errors.append("{}: 已发布文章必须有 title。".format(path))
        if not str(article.get("summary", "")).strip():
            errors.append("{}: 已发布文章必须有 summary。".format(path))
        if not str(article.get("body_markdown", "")).strip():
            errors.append("{}: 已发布文章必须有 body_markdown。".format(path))
        if not str(article.get("published_at", "")).strip():
            errors.append("{}: 已发布文章必须有 published_at。".format(path))
        if not str(article.get("reviewed_by", "")).strip() or not str(article.get("reviewed_at", "")).strip():
            errors.append("{}: 已发布文章必须记录 reviewed_by 和 reviewed_at。".format(path))
        sources = article.get("sources") or []
        material_note = str(article.get("material_note", "")).strip()
        if not sources and not material_note:
            errors.append("{}: 已发布文章必须提供 sources 或 material_note。".format(path))
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict) or not str(source.get("name", "")).strip():
                errors.append("{}: 第 {} 个 source 缺少 name。".format(path, index))
            elif not str(source.get("url", "")).strip() and not str(source.get("note", "")).strip():
                errors.append("{}: 第 {} 个 source 缺少 url 或 note。".format(path, index))
    return errors


def source_html(article):
    sources = article.get("sources") or []
    material_note = str(article.get("material_note", "")).strip()
    if not sources and not material_note:
        return ""
    parts = ['<section class="article-sources"><h2>参考资料</h2><ul>']
    for source in sources:
        name = html.escape(str(source.get("name", "")).strip())
        url = str(source.get("url", "")).strip()
        note = html.escape(str(source.get("note", "")).strip())
        if url:
            parts.append('<li><a href="{}" target="_blank" rel="noopener noreferrer">{}</a>{}</li>'.format(html.escape(url), name, (" · " + note) if note else ""))
        else:
            parts.append("<li>{}：{}</li>".format(name, note or "未提供公开链接"))
    if material_note:
        parts.append("<li>素材说明：{}</li>".format(html.escape(material_note)))
    parts.append("</ul></section>")
    return "".join(parts)


def render_page(article):
    section = article["section"]
    section_label = SECTION_LABELS[section]
    section_url = SECTION_URLS[section]
    title = html.escape(article["title"])
    summary = html.escape(article["summary"])
    author = html.escape(str(article.get("author", "站长")))
    published_at = html.escape(str(article.get("published_at", "")))
    updated_at = html.escape(str(article.get("updated_at", "")))
    reviewed_by = html.escape(str(article.get("reviewed_by", "")))
    reviewed_at = html.escape(str(article.get("reviewed_at", "")))
    body = markdown_to_html(article.get("body_markdown", ""))
    sources = source_html(article)
    updated_line = "<span>更新：{}</span>".format(updated_at) if updated_at else ""
    review_line = "<span>审核：{} · {}</span>".format(reviewed_by, reviewed_at) if reviewed_by else ""
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{summary}">
  <title>{title} | 财税与AI资讯</title>
  <link rel="stylesheet" href="../assets/css/styles.css">
</head>
<body>
  <a class="skip-link" href="#main">跳到主要内容</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="../index.html" aria-label="财税与AI资讯首页">
        <span class="brand-mark" data-site="brand_mark">税</span>
        <span>
          <span class="brand-title" data-site="site_name">财税与AI资讯</span>
          <span class="brand-sub" data-site="tagline">Tax · Finance · AI</span>
        </span>
      </a>
      <nav class="nav" aria-label="主导航">
        <a href="../index.html">首页</a>
        <a href="../about.html">站长介绍</a>
        <a href="../tax-law.html">财税普法</a>
        <a href="../ai.html">AI 赋能</a>
      </nav>
    </div>
  </header>
  <main id="main">
    <section class="page-hero">
      <div class="container">
        <div class="eyebrow">{section_label}</div>
        <h1>{title}</h1>
        <p>{summary}</p>
        <div class="article-meta-line">
          <span>发布：{published_at}</span>
          {updated_line}
          <span>作者：{author}</span>
          {review_line}
        </div>
      </div>
    </section>
    <section class="section">
      <div class="container split">
        <article class="content-card article-body">
          {body}
          {sources}
        </article>
        <aside class="side-card">
          <h2>栏目说明</h2>
          <p>本文基于站长提供的素材或公开文件整理。政策口径、法规名称和具体操作请以原文及主管机关最新发布为准。</p>
          <p><a href="{section_url}">← 返回{section_label}</a></p>
        </aside>
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="container footer-inner">
      <p>? <span data-current-year>2026</span> 财税与AI资讯 · 个人静态站点</p>
      <div class="footer-links">
        <a href="../index.html">首页</a>
        <a href="../about.html">关于本站</a>
        <a href="../tax-law.html">财税普法</a>
        <a href="../ai.html">AI 赋能</a>
      </div>
    </div>
  </footer>
  <script src="../data/site-data.js"></script>
  <script src="../assets/js/site.js"></script>
</body>
</html>
""".format(
        summary=summary,
        title=title,
        section_label=section_label,
        published_at=published_at,
        updated_line=updated_line,
        author=author,
        review_line=review_line,
        body=body,
        sources=sources,
        section_url=section_url,
    )


def main():
    all_articles = load_articles()
    errors = []
    seen_slugs = set()
    published = []

    for article in all_articles:
        errors.extend(validate_article(article))
        slug = str(article.get("slug", "")).strip()
        if slug:
            if slug in seen_slugs:
                errors.append("{}: slug 重复：{}".format(article.get("__path", "unknown"), slug))
            seen_slugs.add(slug)
        if str(article.get("status", "draft")).strip() == "published":
            published.append(article)

    if errors:
        print("文章校验失败：")
        for error in errors:
            print("- " + error)
        return 1

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    manifest_path = ARTICLES_DIR / ".generated.json"
    old_manifest = []
    if manifest_path.exists():
        try:
            old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            old_manifest = []

    list_items = []
    new_slugs = set()
    for article in published:
        slug = article["slug"]
        new_slugs.add(slug)
        page_path = ARTICLES_DIR / (slug + ".html")
        page_path.write_text(render_page(article), encoding="utf-8")
        list_items.append({
            "slug": slug,
            "section": article["section"],
            "title": article["title"],
            "summary": article["summary"],
            "published_at": article.get("published_at", ""),
            "updated_at": article.get("updated_at", ""),
            "author": article.get("author", "站长"),
            "url": "articles/{}.html".format(slug),
        })

    for old_slug in old_manifest:
        if old_slug in new_slugs:
            continue
        old_path = ARTICLES_DIR / (str(old_slug) + ".html")
        try:
            if old_path.exists() and old_path.resolve().parent == ARTICLES_DIR.resolve():
                old_path.unlink()
        except Exception as error:
            print("警告：无法清理旧文章页 {}：{}".format(old_path, error))

    manifest_path.write_text(json.dumps(sorted(new_slugs), ensure_ascii=False, indent=2), encoding="utf-8")

    now = datetime.now(SHANGHAI)
    payload = {
        "generated_at": now.isoformat(timespec="seconds"),
        "generated_at_display": now.strftime("%Y-%m-%d %H:%M"),
        "articles": list_items,
    }
    dumped = json.dumps(payload, ensure_ascii=False, indent=2)
    (DATA_DIR / "articles.json").write_text(dumped + "\n", encoding="utf-8")
    (DATA_DIR / "articles-data.js").write_text("window.ARTICLES_DATA = " + dumped + ";\n", encoding="utf-8")

    print("文章构建完成：已发布 {} 篇".format(len(list_items)))
    for article in all_articles:
        status = article.get("status", "draft")
        if status != "published":
            print("- 跳过 {}（{}）".format(article.get("title") or article.get("slug") or "未命名", status))
    return 0


if __name__ == "__main__":

    sys.exit(main())