# Crawler

本目录用于存放政策网站爬虫代码，目标是把官方政策文件抓取后写入 MySQL 的 `policy_document` 表，并可进一步从政策原文中自动拆解 `policy_item` 候选项。

当前自动拆解是规则版，适合生成第一版结构化措施数据，正式使用前建议人工复核。后续可以继续接入 AI 辅助抽取，提高准确率。

## Directory Structure

```text
crawler/
├── README.md
├── requirements.txt
├── .env.example
├── run.py
├── crawler/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── utils.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── policy_item_extractor.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── html_parser.py
│   └── spiders/
│       ├── __init__.py
│       └── xiamen_hrss.py
└── data/
    └── .gitkeep
```

## File Responsibilities

| 文件/目录 | 作用 |
| --- | --- |
| `requirements.txt` | Python 依赖列表 |
| `.env.example` | 数据库连接配置示例 |
| `run.py` | 爬虫运行入口 |
| `crawler/config.py` | 读取配置，比如数据库地址、用户名、密码 |
| `crawler/db.py` | 负责连接 MySQL 和写入数据 |
| `crawler/models.py` | 定义政策文件、政策链接、政策措施候选项等数据对象 |
| `crawler/utils.py` | 通用工具函数，比如日期解析、文本清洗、请求头 |
| `crawler/extractors/` | 从政策原文中自动拆解 `policy_item` 候选项 |
| `crawler/parsers/` | 页面解析逻辑，比如从 HTML 中提取标题、日期、正文 |
| `crawler/spiders/` | 具体网站爬虫，比如厦门市人社局爬虫 |
| `data/` | 临时保存抓取样本、调试文件或导出结果 |
| `docs/official_sources.md` | 官方政策数据源清单和爬取优先级 |

## Suggested Workflow

1. 先选定一个政策来源网站。
2. 在 `spiders/` 中写该网站的列表页和详情页抓取逻辑。
3. 在 `parsers/` 中写页面字段提取逻辑。
4. 在 `db.py` 中把结果写入 `policy_document`。
5. 从 `policy_document.full_text` 自动拆解 `policy_item` 候选项。
6. 写入 `policy_item`，并通过 `document_item` 记录来源依据。
7. 用 `source_url` 和同一政策文件下的 `item_name` 做基础去重。

## Run

安装依赖：

```bash
pip install -r crawler/requirements.txt
```

先预览抓取结果，不写入数据库：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 5
```

只保留和毕业生就业创业更相关的结果：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 10 --relevant-only
```

抓取更多官方来源：

```bash
python crawler/run.py --source fujian-hrss --max-pages 1 --max-items 10 --relevant-only
python crawler/run.py --source xiamen-gov --max-pages 1 --max-items 10 --relevant-only
python crawler/run.py --source district-gov --max-pages 1 --max-items 10 --relevant-only
python crawler/run.py --source official-sites --max-pages 1 --max-items 30 --relevant-only
```

如果只想抓列表页，不抓手动挑选的专题页：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 10 --skip-static
```

确认结果正常后，复制 `.env.example` 为 `.env` 并填写数据库账号密码，再写入 MySQL：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 5 --save
```

边爬政策原文，边预览自动拆解出的 `policy_item` 候选项：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 5 --relevant-only --extract-items
```

边爬边写入 `policy_document`，同时写入自动拆解出的 `policy_item` 和 `document_item` 关联：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 5 --relevant-only --extract-items --save
```

从数据库已有的 `policy_document` 里拆解 `policy_item`，先预览不入库：

```bash
python crawler/run.py --extract-from-db --max-items 5
```

从数据库已有的 `policy_document` 里拆解并写入 `policy_item`：

```bash
python crawler/run.py --extract-from-db --max-items 5 --save
```

只处理某一条政策文件：

```bash
python crawler/run.py --extract-from-db --document-id 1 --save
```

当前自动拆解是规则版，会根据标题、段落、小标题和关键词生成候选措施。结果适合作为第一版结构化数据，正式使用前建议人工复核。

预览疑似噪声 `policy_item`，比如表头、机构名称、目录项：

```bash
python crawler/run.py --review-noisy-items --max-items 100
```

将疑似噪声项标记为 `review_noise`，不会删除数据：

```bash
python crawler/run.py --review-noisy-items --max-items 100 --save
```

执行第二轮综合清洗：标记明显噪声项，并修正少量明确的分类偏差：

```bash
python crawler/run.py --clean-items --max-items 300
python crawler/run.py --clean-items --max-items 300 --save
```

预览 `policy_item` 到 `item_region` 的地区匹配：

```bash
python crawler/run.py --backfill-regions --max-items 100
```

写入 `item_region` 地区适用关系：

```bash
python crawler/run.py --backfill-regions --max-items 100 --save
```

如果看到类似 SSL、RemoteDisconnected、Connection aborted 的错误，通常是当前网络、代理或政务网站访问策略导致的。可以先确认浏览器能否打开：

```text
https://hrss.xm.gov.cn/xxgk/zcfg/
https://hrss.xm.gov.cn/xxgk/tzgg/
```

爬虫默认会关闭 `requests` 的环境代理，并在 HTTPS 失败时尝试 HTTP，但有些环境仍可能被目标网站断开连接。

## Target Tables

原文抓取阶段写入：

```text
policy_document
```

核心字段：

```text
title
policy_number
issuing_department
publish_level
publish_date
source_url
full_text
summary
status
```

自动拆解阶段写入：

```text
policy_item
document_item
item_region
```

其中 `policy_item` 保存措施名称、分类、对象、条件、补贴标准、办理材料、流程、渠道等字段；`document_item` 保存该措施来自哪一篇政策原文，以及抽取时使用的原文片段；`item_region` 保存措施适用地区。
