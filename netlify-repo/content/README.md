# 文章源文件与发布流程

`content/articles/` 是文章源文件目录，不会被打包进公开站点。只有 `status` 为 `published` 且通过校验的文章，才会由脚本生成到 `site/articles/`。

## 新建文章

复制模板：

```bat
copy content\templates\article-template.json content\articles\my-article.json
```

然后填写字段。建议一篇文件只放一篇文章。

## 字段说明

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `slug` | 是 | 小写字母、数字、短横线，决定文章页文件名 |
| `section` | 是 | `tax-law` 或 `ai` |
| `status` | 是 | `draft`、`review`、`published` |
| `title` | 发布时必填 | 文章标题 |
| `summary` | 发布时必填 | 列表页摘要，避免写成政策结论 |
| `author` | 否 | 默认“站长” |
| `published_at` | 发布时必填 | 日期，建议 `YYYY-MM-DD` |
| `updated_at` | 否 | 更新日期 |
| `reviewed_by` | 发布时必填 | 审核人 |
| `reviewed_at` | 发布时必填 | 审核日期 |
| `material_note` | 条件必填 | 没有公开来源时，说明素材来源和授权情况 |
| `sources` | 条件必填 | 官方文件、原文链接或站长提供的材料 |
| `body_markdown` | 发布时必填 | 文章正文，支持基础 Markdown |

`published` 状态必须同时具备：标题、摘要、正文、发布日期、审核人、审核日期，以及 `sources` 或 `material_note`。

## 写作边界

- 财税文章必须先有官方文件或站长素材。
- 法规名称、文号、税率和期限必须能核验。
- 明确区分“原文规定”和“本站解读”。
- AI 工具文章必须基于真实使用记录，不写未经验证的产品能力。
- 不放入客户隐私、商业秘密或未脱敏数据。
- 不把 AI 生成内容标注为“官方”或“权威”。

## 构建

```bat
py -3 scripts\build_articles.py
```

或双击 `build_articles.bat`。

构建成功后：

- 已发布文章生成到 `site/articles/<slug>.html`
- 列表数据生成到 `site/data/articles.json`
- 页面加载数据生成到 `site/data/articles-data.js`
- `draft` 和 `review` 状态只保留在 `content/articles/`，不会出现在公开页面

如果校验失败，脚本会列出具体字段问题并停止，不会生成半成品页面。

## 建议流程

1. `draft`：基于素材起草。
2. `review`：交给站长审核依据、措辞和引用范围。
3. `published`：补全审核信息后构建发布。

