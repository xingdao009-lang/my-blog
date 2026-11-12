# Netlify 部署说明

当前网站是纯静态站，适合 Netlify。后台 `admin/` 只在本机运行，不随 Netlify 发布。

## 方式一：Netlify Drop（最快）

1. 打开 [Netlify Drop](https://app.netlify.com/drop)。
2. 解压交付包后，找到 `site` 文件夹。
3. 把整个 `site` 文件夹拖进 Netlify Drop。
4. 等待部署完成，Netlify 会给出一个 `https://随机名称.netlify.app` 地址。
5. 打开地址检查：
   - 首页新闻是否显示
   - 站长介绍页是否显示后台保存的内容
   - 财税普法、AI 赋能页面能否打开
   - 新闻原文链接能否跳转

注意：拖拽的是 `site` 文件夹本身，不是整个项目根目录，也不要拖 `admin`、`content` 或 `scripts`。

也可以使用交付包里的 `netlify-site.zip`，它的根目录已经就是网站内容。

## 方式二：GitHub + Netlify 自动部署

1. 把项目根目录提交到 GitHub。
2. 在 Netlify 选择 **Add new site → Import an existing project**。
3. 连接仓库。
4. Build command 留空。
5. Publish directory 填：

```text
site
```

项目根目录的 `netlify.toml` 已经写好 `publish = "site"`，Netlify 会自动读取。

## 后台修改后如何更新线上

Netlify 是静态托管，后台保存不会自动推送到 Netlify。推荐流程：

1. 本机双击 `start_admin.bat`。
2. 在 `http://127.0.0.1:8090/admin` 修改站长介绍或视觉。
3. 点击“保存并同步”。
4. 如需更新新闻，双击 `update_news.bat`。
5. 如果新增文章，双击 `build_articles.bat`。
6. 到 Netlify 重新拖拽 `site` 文件夹，或推送 Git 提交触发自动部署。

如果希望“后台保存后线上自动更新”，需要继续接入 Netlify Identity、Netlify Functions 和外部数据库；当前版本没有把后台暴露到公网，避免安全风险。

## 域名与 HTTPS

没有域名时，先用 Netlify 提供的 `*.netlify.app` 地址。

以后购买域名后：

1. 进入 Netlify 站点 **Domain management**。
2. 点击 **Add a domain**。
3. 按提示在域名服务商处添加 DNS 记录。
4. Netlify 会自动签发 HTTPS 证书。

如果后续部署到中国大陆服务器，则需要另外处理备案和隐私/版权声明；Netlify 部署本身不涉及备案。

## 发布包说明

- `netlify.toml`：Git 部署配置，发布目录为 `site`
- `site/_headers`：Netlify 缓存与安全响应头
- `netlify-site.zip`：可直接拖拽的静态站点包
- `admin/`、`content/`、`scripts/`：本地内容和工具，不应上传到公开站点目录

## 上线检查清单

- [ ] 首页 200，新闻卡片可见
- [ ] 分类筛选正常
- [ ] 来源状态可见
- [ ] 站长介绍内容正确
- [ ] 财税普法 / AI 赋能页面正常
- [ ] 原文链接可打开
- [ ] 联系方式和版权信息正确
- [ ] 手机宽度下导航和卡片不溢出

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
