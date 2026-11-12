(function () {
  var data = window.NEWS_DATA || { generated_at: "", generated_at_display: "尚未更新", items: [], sources: [] };
  var state = { filter: "all" };
  var grid = document.getElementById("news-grid");
  var empty = document.getElementById("news-empty");
  var countEl = document.getElementById("news-count");
  var updatedEl = document.getElementById("last-updated");
  var sourceList = document.getElementById("source-list");
  var filterEls = document.querySelectorAll("[data-filter]");

  var categoryLabels = {
    domestic: "国内财税",
    international: "国际税务",
    finance: "金融快报"
  };
  var categoryClasses = {
    domestic: "badge-domestic",
    international: "badge-international",
    finance: "badge-finance"
  };
  var statusLabels = { ok: "正常", warn: "部分可用", error: "源异常" };

  function escapeHtml(value) {
    return String(value === null || value === undefined ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function formatDate(value) {
    if (!value) return "日期以原文为准";
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
  }

  function itemMatches(item) {
    return state.filter === "all" || item.category === state.filter;
  }

  function renderNews() {
    if (!grid) return;
    var items = (data.items || []).filter(itemMatches);
    if (countEl) countEl.textContent = String(items.length);
    if (!items.length) {
      grid.innerHTML = "";
      if (empty) {
        empty.classList.remove("hidden");
        empty.querySelector("h3").textContent = "当前分类暂无可用新闻";
        empty.querySelector("p").textContent = "数据源异常或尚未完成首次抓取。请查看下方源状态，或运行更新脚本。";
      }
      return;
    }
    if (empty) empty.classList.add("hidden");
    grid.innerHTML = items.map(function (item) {
      var category = categoryLabels[item.category] || "资讯";
      var badgeClass = categoryClasses[item.category] || "badge-domestic";
      var title = escapeHtml(item.title);
      var url = escapeHtml(item.url);
      var source = escapeHtml(item.source);
      var summary = escapeHtml(item.summary || "详情以原文为准。");
      var date = escapeHtml(formatDate(item.published_at));
      return '<article class="news-card">' +
        '<div class="card-top">' +
          '<span class="badge ' + badgeClass + '">' + category + '</span>' +
          '<time class="news-date" datetime="' + escapeHtml(item.published_at || "") + '">' + date + '</time>' +
        '</div>' +
        '<h3><a href="' + url + '" target="_blank" rel="noopener noreferrer">' + title + '</a></h3>' +
        '<p>' + summary + '</p>' +
        '<div class="card-bottom">' +
          '<span class="source">' + source + '</span>' +
          '<a class="read-link" href="' + url + '" target="_blank" rel="noopener noreferrer">查看原文 →</a>' +
        '</div>' +
      '</article>';
    }).join("");
  }

  function renderSources() {
    if (!sourceList) return;
    var sources = data.sources || [];
    if (!sources.length) {
      sourceList.innerHTML = '<div class="source-item"><span class="status-dot warn"></span><div><h3>暂无源状态</h3><p>请运行更新脚本生成数据。</p></div></div>';
      return;
    }
    sourceList.innerHTML = sources.map(function (source) {
      var status = source.status || "error";
      var statusText = statusLabels[status] || "未知";
      var detail = source.message || (status === "ok" ? "抓取正常" : "来源暂不可用");
      var countText = typeof source.count === "number" ? " · " + source.count + " 条" : "";
      return '<div class="source-item">' +
        '<span class="status-dot ' + escapeHtml(status) + '"></span>' +
        '<div><h3>' + escapeHtml(source.name) + ' · ' + statusText + countText + '</h3>' +
        '<p>' + escapeHtml(detail) + '</p>' +
        '<a href="' + escapeHtml(source.url) + '" target="_blank" rel="noopener noreferrer">访问来源</a></div>' +
      '</div>';
    }).join("");
  }

  filterEls.forEach(function (btn) {
    btn.addEventListener("click", function () {
      state.filter = btn.getAttribute("data-filter") || "all";
      filterEls.forEach(function (el) { el.classList.toggle("is-active", el === btn); });
      renderNews();
    });
  });

  if (updatedEl) updatedEl.textContent = data.generated_at_display || "尚未更新";
  renderNews();
  renderSources();

})();