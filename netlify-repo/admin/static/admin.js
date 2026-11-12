(function () {
  var $ = function (id) { return document.getElementById(id); };
  var csrf = "";
  var textFields = [
    "site_name", "brand_mark", "tagline", "hero_title", "hero_subtitle",
    "about_title", "about_lead", "name", "role", "bio", "contact",
    "avatar", "footer_text"
  ];

  function show(element) { if (element) element.classList.remove("hidden"); }
  function hide(element) { if (element) element.classList.add("hidden"); }
  function authMessage(text, isError) {
    var el = $("auth-message");
    if (!el) return;
    el.textContent = text || "";
    el.style.color = isError ? "#b42318" : "#15803d";
  }
  function statusMessage(text, isError) {
    var el = $("status-bar");
    if (!el) return;
    el.textContent = text || "";
    el.classList.toggle("error", Boolean(isError));
  }

  async function request(path, options) {
    options = options || {};
    var headers = options.headers || {};
    headers["X-CSRF-Token"] = csrf;
    if (options.body) headers["Content-Type"] = "application/json";
    var response = await fetch(path, {
      method: options.method || "GET",
      credentials: "same-origin",
      headers: headers,
      body: options.body
    });
    var data = {};
    try { data = await response.json(); } catch (error) { data = {}; }
    if (!response.ok) throw new Error(data.error || "请求失败，请重试");
    return data;
  }

  function showSetup() {
    hide($("login-block"));
    show($("setup-block"));
    show($("auth-screen"));
    hide($("dashboard"));
  }

  function showLogin() {
    hide($("setup-block"));
    show($("login-block"));
    show($("auth-screen"));
    hide($("dashboard"));
  }

  async function enterDashboard() {
    hide($("auth-screen"));
    show($("dashboard"));
    var data = await request("/admin/api/settings");
    fillForm(data.settings || {});
    updatePreview();
  }

  function fillForm(settings) {
    textFields.forEach(function (key) {
      var input = $(key);
      if (input) input.value = settings[key] || "";
    });
    var focus = settings.focus || [];
    $("focus").value = Array.isArray(focus) ? focus.join("，") : String(focus || "");
    var accent = settings.accent || "#1d4ed8";
    $("accent").value = accent;
    $("accent_text").value = accent;
    $("theme").value = settings.theme || "business-blue";
  }

  function currentSettings() {
    var settings = {};
    textFields.forEach(function (key) {
      settings[key] = ($(key) && $(key).value ? $(key).value.trim() : "");
    });
    settings.focus = ($("focus").value || "").split(/[,，\n]/).map(function (item) { return item.trim(); }).filter(Boolean);
    settings.accent = ($("accent_text").value || $("accent").value || "#1d4ed8").trim();
    settings.theme = $("theme").value;
    return settings;
  }

  function updatePreview() {
    var settings = currentSettings();
    $("preview-site").textContent = settings.site_name || "站点名称";
    $("preview-avatar").textContent = settings.avatar || settings.brand_mark || "站";
    $("preview-name").textContent = settings.name || "站长";
    $("preview-role").textContent = settings.role || "身份/方向";
    $("preview-bio").textContent = (settings.bio || "这里显示站长简介。").split(/\n+/)[0];
    $("preview-contact").textContent = settings.contact || "这里显示联系方式。";
    var chips = $("preview-focus");
    chips.innerHTML = "";
    (settings.focus.length ? settings.focus : ["财税合规", "AI 办公"]).forEach(function (item) {
      var chip = document.createElement("span");
      chip.textContent = item;
      chips.appendChild(chip);
    });
    var accent = /^#[0-9a-fA-F]{6}$/.test(settings.accent) ? settings.accent : "#1d4ed8";
    document.documentElement.style.setProperty("--admin-accent", accent);
    var backgrounds = {
      "business-blue": "radial-gradient(circle at 85% 10%, rgba(255,255,255,0.24), transparent 32%), linear-gradient(145deg, #0b2545, #164e93)",
      "midnight": "radial-gradient(circle at 85% 10%, rgba(147,197,253,0.20), transparent 32%), linear-gradient(145deg, #06162b, #0c2c55)",
      "slate": "radial-gradient(circle at 85% 10%, rgba(255,255,255,0.18), transparent 32%), linear-gradient(145deg, #263445, #4b5f76)"
    };
    $("preview-shell").style.background = backgrounds[settings.theme] || backgrounds["business-blue"];
  }

  async function saveSettings() {
    try {
      var settings = currentSettings();
      if (!/^#[0-9a-fA-F]{6}$/.test(settings.accent)) throw new Error("主色调格式应为 #RRGGBB");
      statusMessage("保存中…", false);
      await request("/admin/api/settings", { method: "POST", body: JSON.stringify(settings) });
      statusMessage("已保存并同步到前台。", false);
      updatePreview();
    } catch (error) {
      statusMessage(error.message, true);
    }
  }

  async function boot() {
    try {
      var status = await request("/admin/api/status");
      if (!status.configured) {
        showSetup();
        return;
      }
      if (status.authenticated) {
        csrf = status.csrf || "";
        await enterDashboard();
      } else {
        showLogin();
      }
    } catch (error) {
      showLogin();
      authMessage(error.message, true);
    }
  }

  $("setup-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    var password = $("setup-password").value;
    var confirm = $("setup-confirm").value;
    if (password !== confirm) {
      authMessage("两次输入的密码不一致。", true);
      return;
    }
    try {
      var result = await request("/admin/api/setup", { method: "POST", body: JSON.stringify({ password: password }) });
      csrf = result.csrf || "";
      authMessage("管理员密码已创建。", false);
      await enterDashboard();
    } catch (error) {
      authMessage(error.message, true);
    }
  });

  $("login-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    try {
      var result = await request("/admin/api/login", { method: "POST", body: JSON.stringify({ password: $("login-password").value }) });
      csrf = result.csrf || "";
      authMessage("", false);
      await enterDashboard();
    } catch (error) {
      authMessage(error.message, true);
    }
  });

  $("logout-btn").addEventListener("click", async function () {
    try { await request("/admin/api/logout", { method: "POST", body: "{}" }); } catch (error) {}
    csrf = "";
    showLogin();
  });

  $("save-btn").addEventListener("click", saveSettings);

  $("accent").addEventListener("input", function () {
    $("accent_text").value = $("accent").value;
    updatePreview();
  });
  $("accent_text").addEventListener("input", function () {
    if (/^#[0-9a-fA-F]{6}$/.test($("accent_text").value)) $("accent").value = $("accent_text").value;
    updatePreview();
  });

  document.querySelectorAll(".editor input, .editor textarea, .editor select").forEach(function (input) {
    input.addEventListener("input", updatePreview);
    input.addEventListener("change", updatePreview);
  });

  boot();

})();