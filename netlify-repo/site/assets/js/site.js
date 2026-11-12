(function () {
  var data = window.SITE_DATA || {};
  var root = document.documentElement;
 root.classList.add("js");

  function setText(key, value) {
    if (value === undefined || value === null || value === "") return;
    document.querySelectorAll('[data-site="' + key + '"]').forEach(function (el) {
      el.textContent = String(value);
    });
  }

  function applyProfile() {
    var keys = ["site_name", "brand_mark", "tagline", "hero_title", "hero_subtitle", "about_title", "about_lead", "name", "role", "contact", "avatar", "footer_text"];
    keys.forEach(function (key) { setText(key, data[key]); });

    var accent = /^#[0-9a-fA-F]{6}$/.test(data.accent || "") ? data.accent : "#1d4ed8";
    root.style.setProperty("--accent", accent);
    root.style.setProperty("--blue", accent);
    root.setAttribute("data-theme", data.theme || "business-blue");

    document.querySelectorAll("[data-site-bio]").forEach(function (el) {
      el.innerHTML = "";
      String(data.bio || "").split(/\n+/).forEach(function (paragraph) {
        if (!paragraph.trim()) return;
        var p = document.createElement("p");
        p.textContent = paragraph.trim();
        el.appendChild(p);
      });
    });

    document.querySelectorAll("[data-site-focus]").forEach(function (el) {
      el.innerHTML = "";
      (Array.isArray(data.focus) ? data.focus : []).forEach(function (item) {
        var node = document.createElement(el.tagName === "UL" ? "li" : "span");
        node.textContent = item;
        if (el.tagName !== "UL") node.className = "meta-chip";
        el.appendChild(node);
      });
    });

    if (data.site_name && document.title.indexOf("财税与AI资讯") !== -1) {
      document.title = document.title.replace("财税与AI资讯", data.site_name);
    }
    if (data.footer_text) {
      document.querySelectorAll("[data-footer-text]").forEach(function (el) { el.textContent = data.footer_text; });
    }
  }

  applyProfile();

  document.querySelectorAll("[data-current-year]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

})();