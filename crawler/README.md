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

## Suggested Workflow

1. 先选定一个政策来源网站。
2. 在 `spiders/` 中写该网站的列表页和详情页抓取逻辑。
3. 在 `parsers/` 中写页面字段提取逻辑。
4. 在 `db.py` 中把结果写入 `policy_document`。
5. 用 `source_url` 做去重，避免重复入库。

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

