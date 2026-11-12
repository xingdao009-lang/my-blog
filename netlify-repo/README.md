# 财税与AI资讯

第一阶段交付：可直接本地运行的静态网站 + 新闻聚合更新脚本。当前版本重点跑通“四页框架 + 新闻抓取 + 来源状态”流程，普法与 AI 栏目暂不自动生成文章。

## 目录结构

```text
site/
  index.html              首页：新闻聚合
  about.html              站长介绍
  tax-law.html            财税普法栏目框架
  ai.html                 AI 赋能栏目框架
  assets/css/styles.css   全站样式
  assets/js/site.js       通用脚本
  assets/js/news.js       新闻渲染与筛选
  data/news.json          新闻数据（UTF-8）
  data/news-data.js       供页面直接加载的新闻数据
scripts/
  update_news.py          公开新闻抓取器
  install_schedule.ps1    创建每日定时任务
update_news.bat           手动更新新闻
serve.bat                 本地预览服务器
```

## 本地运行

### 方式一：直接打开

双击 `site/index.html`。页面使用本地 `news-data.js`，不依赖浏览器跨站请求，直接打开也能展示新闻。

### 方式二：本地服务器（推荐）

双击 `serve.bat`，然后打开：

```text
http://127.0.0.1:8080/
```

按 `Ctrl+C` 停止服务器。

## 更新新闻

双击 `update_news.bat`，或在命令行运行：

```bat
py -3 scripts\update_news.py
```

脚本会重新抓取公开来源，并生成：

- `site/data/news.json`
- `site/data/news-data.js`

如果所有来源都没有解析到条目，脚本会返回失败，并保留上一版数据，避免把页面清空。

## 每日定时更新

使用 Windows 当前用户创建一个每天 08:30 运行的任务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_schedule.ps1
```

也可以指定时间：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_schedule.ps1 -Time "09:00"
```

任务名称为 `TaxAI-News-Update`。可在 Windows“任务计划程序”中查看、修改或删除。若系统权限策略不允许创建任务，请用管理员 PowerShell 运行。

## 当前新闻源状态（2026-11-11 核验）

| 来源 | 状态 | 说明 |
| --- | --- | --- |
| 国家税务总局 | 正常 | 读取官网首页公开新闻链接，并访问文章页读取发布日期 |
| 新华财经 | 正常 | 读取新华财经公开首页的财经文章链接，日期取自文章 URL |
| 中国人民银行 | 正常 | 读取“沟通交流”公开页面的新闻标题与日期 |
| OECD | 源异常 | 官方页面返回 HTTP 403（反爬/访问限制） |
| Wolters Kluwer | 源异常 | 官方页面返回 HTTP 403（反爬/访问限制） |

国际税务来源异常时，页面会显示“源异常”，不会用其他内容替代，也不会编造国际新闻。后续若你提供可公开访问的 RSS 或正式授权接口，可在 `scripts/update_news.py` 中增加解析器。

安全说明：检测中发现 `tax-news.com` 域名当前展示的内容已不是正常的 Tax-news 新闻页，因此没有把它作为 Wolters Kluwer 的数据源。

## 内容发布流程

“财税普法”和“AI 赋能”栏目目前只搭框架，不自动发布文章。建议流程：

1. 站长提供官方文件、原文链接、核心要点、目标读者和案例素材。
2. 助手基于材料起草，逐条标注依据。
3. 站长审核法规名称、文号、税率、期限和引用范围。
4. 确认后再写入文章页面并发布。

涉及政策解读时，不把 AI 生成内容标注为“官方”或“权威”。

## 部署到静态托管平台

`site/` 是完整静态站点，无后端依赖。可上传到：

- Nginx / Apache 服务器：将 `site/` 内容作为站点根目录。
- Vercel / Netlify / Cloudflare Pages：项目根目录选择本目录，输出目录填 `site`。
- 对象存储静态托管：上传 `site/` 下全部文件，入口设为 `index.html`。

当前暂无域名，可先使用平台默认地址。绑定域名后需配置 DNS 和 HTTPS；若部署到中国大陆服务器，还需按实际要求处理备案与隐私/版权声明。

## 后续可继续做

1. 补充站长真实姓名、简介、头像和联系方式。
2. 确认域名与部署环境后，给出对应平台的具体上线步骤。
3. 提供普法/AI 文章素材，逐篇起草并按草稿清单审核。

## 第二阶段：文章发布流程

已增加基于 JSON 源文件的文章发布框架：

```text
content/
  articles/                 文章源文件，不会被公开托管
  templates/                文章模板
  README.md                 字段与审核流程说明
scripts/build_articles.py   校验并生成已审核文章
build_articles.bat          手动构建文章
site/articles/              构建生成的公开文章页
site/data/articles.json     已发布文章列表
site/data/articles-data.js  页面加载数据
```

使用方式：

1. 复制 `content/templates/article-template.json` 到 `content/articles/`。
2. 按 `content/README.md` 填写标题、摘要、正文、来源和审核信息。
3. 先保持 `status` 为 `draft` 或 `review`。
4. 站长审核后改为 `published`，补全 `reviewed_by` 和 `reviewed_at`。
5. 双击 `build_articles.bat` 生成公开文章页。


## 本地内容后台

新增了一个无需数据库的本地后台：

```text
start_admin.bat             启动后台
admin/server.py             后台服务
admin/static/               后台页面
content/site.json           站点文案与主题源文件
site/data/site.json         前台读取的配置
site/data/site-data.js      前台加载数据
```

### 使用步骤

1. 双击 `start_admin.bat`。
2. 浏览器打开 `http://127.0.0.1:8090/admin`。
3. 首次访问时创建管理员密码，至少 8 个字符。
4. 修改站点名称、首页文案、站长介绍、关注方向、联系方式和主色调。
5. 点击“保存并同步”，刷新前台页面即可看到更新。

后台默认只绑定 `127.0.0.1`，局域网或公网无法直接访问。不要把这个端口反向代理到公网；如果以后需要远程管理，应先增加 HTTPS、登录限流和更完整的权限控制。


## 全自动更新（推荐）

如果使用 GitHub + Netlify，不要用 Netlify Drop 做日常更新。正确方式是把项目连接到 GitHub，让 Netlify 在每次提交后自动部署。

项目内已经包含：

```text
.github/workflows/update-site.yml
scripts/update_all.py
```

工作流会：

1. 每天北京时间 08:30 自动运行，也可以在 GitHub Actions 页面手动触发。
2. 抓取公开新闻。
3. 同步后台保存的站点配置。
4. 构建已审核文章。
5. 将 `site/data` 和 `site/articles` 的变更提交回仓库。
6. Netlify 监听 GitHub 提交后自动重新部署。

本地也可以手动执行：

```text
update_all.bat
```

### 文章自动化的边界

新闻可以全自动更新。

普法与 AI 文章可以自动构建，但不会自动把 `draft` 或 `review` 状态的文章发布出去。文章必须先由站长审核，改为 `published` 并填写审核人和审核日期后，下一次自动构建才会发布。这样避免 AI 误读政策或把未经核验的内容上线。

如果后续需要“自动抓官方原文并生成待审核草稿”，可以在现有文章源文件流程上继续加素材导入器；仍然建议保留人工审核这一道。

### GitHub 设置

1. 把项目推送到 GitHub 仓库。
2. 在 Netlify 中连接该仓库，发布目录填 `site`。
3. 确认 GitHub Actions 有 `contents: write` 权限。
4. 在 GitHub Actions 页面手动运行一次 **Update site content**，确认能提交变更。
