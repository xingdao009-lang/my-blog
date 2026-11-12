(function () {
  var data = window.ARTICLES_DATA || { articles: [] };
  var sections = {
    "tax-law": { list: "tax-article-list", empty: "tax-article-empty" },
    ai: { list: "ai-article-list", empty: "ai-article-empty" }
  };

  function escapeHtml(value) {
    return String(value === null || value === undefined ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function formatDate(value) {
    if (!value) return "日期待补充";
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
  }

  function renderSection(section) {
    var meta = sections[section];
    var list = document.getElementById(meta.list);
    var empty = document.getElementById(meta.empty);
    if (!list) return;
    var items = (data.articles || []).filter(function (item) { return item.section === section; });
    if (!items.length) {
      list.innerHTML = "";
      if (empty) empty.classList.remove("hidden");
      return;
    }
    if (empty) empty.classList.add("hidden");
    list.innerHTML = items.map(function (item) {
      var title = escapeHtml(item.title);
      var url = escapeHtml(item.url);
      var summary = escapeHtml(item.summary);
      var author = escapeHtml(item.author || "站长");
      var published = escapeHtml(formatDate(item.published_at));
      return '<article class="article-card">' +
        '<div>' +
          '<h3><a href="' + url + '">' + title + '</a></h3>' +
          '<p>' + summary + '</p>' +
          '<div class="article-meta">' +
            '<span class="meta-chip">发布 ' + published + '</span>' +
            '<span class="meta-chip">' + author + '</span>' +
          '</div>' +
        '</div>' +
        '<a class="arrow" href="' + url + '" aria-label="阅读文章">→</a>' +
      '</article>';
    }).join("");
  }

  renderSection("tax-law");
  renderSection("ai");

})();