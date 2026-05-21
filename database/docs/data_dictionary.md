# 数据字典

本文档根据项目根目录 `readme.md` 整理，SQL 实现位于：

- `database/migrations/202605211200_initial_schema.sql`
- `database/seeds/202605211210_seed_basic_reference_data.sql`

## 命名说明

README 中的实体名使用概念模型命名，数据库表名使用 `snake_case`：

| README 实体 | 数据库表 |
| --- | --- |
| Policy_Document | `policy_document` |
| Policy_Item | `policy_item` |
| Document_Item | `document_item` |
| Region | `region` |
| Item_Region | `item_region` |
| Category | `category` |
| User | `app_user` |
| Login_Record | `login_record` |
| QA_Record | `qa_record` |
| QA_Reference | `qa_reference` |

`User` 在部分数据库中容易与保留字冲突，因此实际表名使用 `app_user`。

## 核心设计

`policy_document` 保存官方政策文件原文和来源信息，解决“政策依据来自哪里”。

`policy_item` 保存可被用户查询、匹配和解释的具体政策措施，解决“用户能不能申请、申请什么、怎么申请”。

`document_item` 连接政策文件和政策措施。一个政策文件可以拆出多个措施，一个措施也可以有多个政策文件作为依据、修订或废止来源。

`region` 使用自关联保存中国、福建省、厦门市、厦门各区的层级关系。

`item_region` 连接政策措施和适用地区。国家级、省级、市级、区级政策都可以通过这张表表达适用范围。

`qa_record` 保存用户问题和 AI 回答，`qa_reference` 保存回答引用了哪些政策措施，便于展示引用依据和追踪来源。

## 关系摘要

| 关系 | 实现方式 |
| --- | --- |
| 政策文件 N 对 M 政策措施 | `document_item(document_id, item_id)` |
| 政策措施 N 对 1 政策分类 | `policy_item.category_id` |
| 政策措施 N 对 M 地区 | `item_region(item_id, region_id)` |
| 地区 N 对 1 上级地区 | `region.parent_region_id` |
| 用户 1 对 N 登录记录 | `login_record(user_id, login_no)` |
| 用户 1 对 N 问答记录 | `qa_record.user_id` |
| 问答记录 N 对 M 政策措施引用 | `qa_reference(qa_id, item_id)` |

## 执行顺序

先执行建表迁移：

```sql
SOURCE database/migrations/202605211200_initial_schema.sql;
```

再执行基础种子数据：

```sql
SOURCE database/seeds/202605211210_seed_basic_reference_data.sql;
```

## 后续可扩展表

如果后续要做 RAG 或向量检索，建议增加：

| 表名 | 用途 |
| --- | --- |
| `policy_chunk` | 保存政策原文切片、段落编号、原文位置 |
| `policy_embedding` | 保存文本切片或政策措施的向量索引信息 |
| `user_profile` | 保存毕业时间、学历、就业状态、创业状态、社保状态等匹配字段 |
| `match_record` | 保存一次用户画像和政策匹配结果 |
