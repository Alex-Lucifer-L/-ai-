# Crawler

本目录用于存放政策网站爬虫代码，目标是把官方政策文件抓取后写入 MySQL 的 `policy_document` 表。

第一阶段只做“政策原文入库”，暂时不自动拆解 `policy_item`。具体措施拆解可以后续用人工整理、规则抽取或 AI 辅助完成。

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
| `crawler/models.py` | 定义政策文件这类数据对象 |
| `crawler/utils.py` | 通用工具函数，比如日期解析、文本清洗、请求头 |
| `crawler/parsers/` | 页面解析逻辑，比如从 HTML 中提取标题、日期、正文 |
| `crawler/spiders/` | 具体网站爬虫，比如厦门市人社局爬虫 |
| `data/` | 临时保存抓取样本、调试文件或导出结果 |
| `docs/official_sources.md` | 官方政策数据源清单和爬取优先级 |

## Suggested Workflow

1. 先选定一个政策来源网站。
2. 在 `spiders/` 中写该网站的列表页和详情页抓取逻辑。
3. 在 `parsers/` 中写页面字段提取逻辑。
4. 在 `db.py` 中把结果写入 `policy_document`。
5. 用 `source_url` 做去重，避免重复入库。

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

如果只想抓列表页，不抓手动挑选的专题页：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 10 --skip-static
```

确认结果正常后，复制 `.env.example` 为 `.env` 并填写数据库账号密码，再写入 MySQL：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 5 --save
```

如果看到类似 SSL、RemoteDisconnected、Connection aborted 的错误，通常是当前网络、代理或政务网站访问策略导致的。可以先确认浏览器能否打开：

```text
https://hrss.xm.gov.cn/xxgk/zcfg/
https://hrss.xm.gov.cn/xxgk/tzgg/
```

爬虫默认会关闭 `requests` 的环境代理，并在 HTTPS 失败时尝试 HTTP，但有些环境仍可能被目标网站断开连接。

## First Target Table

第一阶段建议只写入：

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
