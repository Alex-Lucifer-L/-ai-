项目名称：
厦门大学生/高校毕业生就业创业政策 AI 解读系统

核心定位：
帮助大学生/毕业生查询、理解、匹配在厦门就业创业时可适用的相关政策。

服务对象：
1. 在校大学生
2. 应届毕业生
3. 离校未就业毕业生
4. 准备来厦门就业的毕业生
5. 准备在厦门创业的毕业生

政策范围：
不再只限于“厦门本地发布的政策”，而是：

1. 国家级政策
2. 福建省级政策
3. 厦门市级政策
4. 厦门各区政策

地区层级：
中国
└── 福建省
    └── 厦门市
        ├── 思明区
        ├── 湖里区
        ├── 集美区
        ├── 海沧区
        ├── 同安区
        └── 翔安区

主要政策方向：
1. 就业补贴
2. 创业扶持
3. 人才补贴
4. 实习 / 见习
5. 职业培训
6. 落户 / 住房相关支持
7. 企业吸纳毕业生补贴

系统核心能力：
1. 政策查询
2. 政策分类查看
3. AI 通俗解读
4. 根据用户情况匹配政策
5. 展示政策来源
6. 判断政策适用层级



政策结构化信息：
政策标题
发布部门
发布层级
适用地区
政策类别
适用对象
政策状态
发布日期
来源链接
政策正文




工作流：
厦门大学生/高校毕业生就业创业政策 AI 解读系统
│
├── 1. 政策数据层
│   ├── 政策文件 Policy_Document
│   │   ├── 原始政策标题
│   │   ├── 发布部门
│   │   ├── 发布时间
│   │   ├── 来源链接
│   │   └── 政策全文
│   │
│   └── 政策措施 Policy_Item
│       ├── 具体补贴/扶持措施
│       ├── 适用对象
│       ├── 适用地区
│       ├── 申请条件
│       ├── 补贴标准
│       └── 办理方式
│
├── 2. 检索层
│   ├── 用户提出问题
│   ├── 系统从数据库查相关政策
│   └── 取出相关政策原文/摘要/措施
│
├── 3. AI 解读层
│   ├── 把用户问题 + 政策内容发给大模型 API
│   ├── 大模型生成通俗解释
│   └── 返回申请条件、补贴内容、注意事项
│
└── 4. 结果展示层
    ├── AI 解读结果
    ├── 相关政策列表
    ├── 原文来源链接
    └── 引用依据


数据库结构：
数据库设计核心
│
├── Policy_Document：保存官方政策文件
│   ├── 文件标题
│   ├── 发布部门
│   ├── 发布层级
│   ├── 发布时间
│   ├── 原文链接
│   └── 政策全文
│
└── Policy_Item：保存用户真正关心的具体措施
    ├── 措施名称
    ├── 所属政策文件
    ├── 政策类别
    ├── 适用地区
    ├── 适用对象
    ├── 申请条件
    ├── 扶持内容
    ├── 办理流程
    └── 注意事项








一、实体列表

1. Policy_Document   政策文件
2. Policy_Item       政策措施
3. Document_Item     政策文件-政策措施依据关系
4. Region            地区
5. Item_Region       政策措施-地区适用关系
6. Category          政策分类
7. User              用户
8. Login_Record      登录记录
9. QA_Record         问答记录
10. QA_Reference     问答引用关系


二、实体类型

强实体：
1. Policy_Document
2. Policy_Item
3. Region
4. Category
5. User
6. QA_Record

弱实体：
1. Login_Record

联系实体 / 中间实体：
1. Document_Item
2. Item_Region
3. QA_Reference

支持联系 / 识别联系：
User 1 ─── 产生 ─── N Login_Record

三、联系列表

1. Policy_Document N ─── 依据 ─── M Policy_Item
   通过 Document_Item / 政策文件-政策措施依据关系实现

2. Policy_Item N ─── 归类于 ─── 1 Category

3. Policy_Item N ─── 适用于 ─── M Region
   通过 Item_Region / 政策措施-地区适用关系实现

4. Region N ─── 隶属于 ─── 1 Region

5. User 1 ─── 产生 ─── N Login_Record
   Login_Record 是弱实体，“产生”是支持联系 / 识别联系

6. User 1 ─── 发起 ─── N QA_Record

7. QA_Record N ─── 引用 ─── M Policy_Item
   通过 QA_Reference / 问答引用关系实现






          

四、实体——属性

1. Policy_Document 政策文件
├── document_id 主键
├── title
├── policy_number
├── issuing_department
├── publish_level
├── publish_date
├── effective_date
├── expire_date
├── status
├── source_url
├── full_text
├── summary
└── created_at


2. Policy_Item 政策措施
├── item_id 主键
├── category_id 外键 → Category.category_id
├── item_name
├── target_group_text
├── conditions_text
├── support_content
├── subsidy_standard
├── application_materials
├── application_process
├── application_channel
├── keywords
├── status
└── created_at


3. Document_Item 政策文件-政策措施依据关系
├── document_id 外键 → Policy_Document.document_id
├── item_id 外键 → Policy_Item.item_id
├── relation_type
├── original_excerpt
├── note
└── 主键：document_id + item_id


4. Region 地区
├── region_id 主键
├── region_name
├── region_level
└── parent_region_id 外键 → Region.region_id


5. Item_Region 政策措施-地区适用关系
├── item_id 外键 → Policy_Item.item_id
├── region_id 外键 → Region.region_id
├── applicability_note
├── applicability_type
└── 主键：item_id + region_id


6. Category 政策分类
├── category_id 主键
├── category_name
└── description


7. User 用户
├── user_id 主键
├── username
├── password_hash
├── role
├── status
├── created_at
└── updated_at


8. Login_Record 登录记录
├── user_id 外键 → User.user_id
├── login_no 局部主键
├── login_time
├── login_ip
├── login_status
└── 主键：user_id + login_no


9. QA_Record 问答记录
├── qa_id 主键
├── user_id 外键 → User.user_id
├── user_question
├── ai_answer
├── question_time
├── answer_time
└── model_name


10. QA_Reference 问答引用关系
├── qa_id 外键 → QA_Record.qa_id
├── item_id 外键 → Policy_Item.item_id
├── relevance_score
├── reference_note
├── used_excerpt
├── rank_order
└── 主键：qa_id + item_id




五、当前已完成工作

在上述设计基础上，目前项目已经完成了数据库脚本、政策爬虫、政策措施自动拆解和地区回填的第一版实现。

1. 数据库脚本

已在 `database/` 目录下建立 MySQL 8 数据库相关文件：

```text
database/
├── migrations/
│   └── 202605211200_initial_schema.sql
├── seeds/
│   └── 202605211210_seed_basic_reference_data.sql
├── docs/
│   └── data_dictionary.md
└── README.md
```

其中：

```text
202605211200_initial_schema.sql
```

用于创建核心表，包括：

```text
policy_document
policy_item
document_item
region
item_region
category
app_user
login_record
qa_record
qa_reference
```

```text
202605211210_seed_basic_reference_data.sql
```

用于插入基础政策分类，以及中国、福建省、厦门市和厦门六个区的地区层级数据。


2. 爬虫模块

已新增 `crawler/` 目录，用于抓取官方政策数据：

```text
crawler/
├── run.py
├── requirements.txt
├── .env.example
├── crawler/
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── utils.py
│   ├── extractors/
│   │   ├── policy_item_extractor.py
│   │   └── region_matcher.py
│   ├── parsers/
│   │   └── html_parser.py
│   └── spiders/
│       └── xiamen_hrss.py
└── docs/
    └── official_sources.md
```

目前已实现厦门市人力资源和社会保障局相关页面的爬取，包含：

```text
就业创业
人才服务
规范性文件
其他政策文件
通知公告
入厦政策专题
毕业生入厦政策指南
优秀毕业生入厦政策
```

同时新增通用政务网站爬虫，已接入更多官方来源：

```text
福建省人力资源和社会保障厅
厦门市人民政府门户网站
集美区人民政府
海沧区人民政府
思明区人民政府
湖里区人民政府
```

新增运行入口包括：

```text
fujian-hrss
xiamen-gov
district-gov
official-sites
```

爬虫可以提取：

```text
政策标题
政策文号
发布部门
发布层级
发布日期
来源链接
政策正文
政策摘要
```

并写入 `policy_document` 表。


3. 政策措施自动拆解

已实现规则版 `policy_item` 自动拆解功能。

系统可以从 `policy_document.full_text` 中自动生成政策措施候选项，并写入：

```text
policy_item
document_item
```

目前可抽取的字段包括：

```text
措施名称
政策分类
适用对象
申请条件
扶持内容
补贴标准
申请材料
办理流程
办理渠道
关键词
原文依据片段
```

说明：当前拆解方式是规则抽取，适合作为第一版结构化数据，正式用于用户展示前仍建议人工复核。


3.1 AI 问答模块

已新增 `ai/` 目录，用于后续接入大模型 API：

```text
ai/
├── ask.py
├── README.md
└── ai/
    ├── config.py
    ├── retriever.py
    ├── prompt_builder.py
    ├── llm_client.py
    └── qa_service.py
```

当前 AI 模块已支持：

```text
从 policy_item 检索相关政策措施
构造带引用依据的 prompt
预览检索结果和 prompt
调用 OpenAI-compatible Chat Completions API
```

可先使用 dry-run 模式测试检索和提示词：

```bash
python ai/ask.py "我是应届毕业生，想在厦门创业，有什么补贴？" --dry-run --top-k 3
```

配置大模型 API Key 后，可直接调用模型生成回答。


4. 地区适用关系回填

已实现 `item_region` 自动回填。

系统会根据政策措施名称、政策内容和发布层级，识别适用地区，例如：

```text
中国
福建省
厦门市
思明区
湖里区
集美区
海沧区
同安区
翔安区
```

并写入 `item_region` 表。


5. 数据质量处理

已实现疑似噪声政策措施识别。

例如表头、培训机构名称、目录项等内容不会直接删除，而是标记为：

```text
review_noise
```

这样可以保留原始抽取结果，同时避免它们混入后续查询和地区匹配。


6. 当前数据库状态

截至当前测试，数据库中已有：

```text
policy_document = 5
policy_item = 36
document_item = 36
item_region = 26
```

其中 `policy_item` 状态为：

```text
effective = 26
review_noise = 10
```


7. 常用运行命令

预览爬虫结果，不写入数据库：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 10 --relevant-only
```

边爬取政策原文，边拆解政策措施，并写入数据库：

```bash
python crawler/run.py --source xiamen-hrss --max-pages 1 --max-items 10 --relevant-only --extract-items --save
```

从已有 `policy_document` 中拆解 `policy_item`：

```bash
python crawler/run.py --extract-from-db --max-items 20 --save
```

识别并标记疑似噪声政策措施：

```bash
python crawler/run.py --review-noisy-items --max-items 100 --save
```

自动回填政策措施适用地区：

```bash
python crawler/run.py --backfill-regions --max-items 100 --save
```


8. 当前阶段总结

目前系统已经完成：

```text
数据库设计
数据库建表脚本
基础分类和地区数据
厦门人社局政策爬虫
福建省人社厅政策爬虫
厦门市政府门户政策爬虫
厦门区级政府政策爬虫
政策原文入库
政策措施规则拆解
政策文件-措施依据关系
政策措施-地区适用关系
疑似噪声数据标记
AI 问答模块骨架
```

尚未完成：

```text
更多官方网站爬虫持续扩展
更精细的政策措施抽取
政策查询接口
用户画像匹配
AI 通俗解读效果优化
问答记录与引用保存
前端展示页面
```
