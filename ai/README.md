# AI

本目录用于接入大模型 API，实现政策问答和通俗解读。

当前阶段先提供最小可用骨架：

```text
用户问题
→ 从 MySQL 检索相关 policy_item
→ 构造带引用依据的 prompt
→ 调用大模型 API
→ 输出回答
```

## Directory Structure

```text
ai/
├── README.md
├── ask.py
└── ai/
    ├── __init__.py
    ├── config.py
    ├── llm_client.py
    ├── prompt_builder.py
    ├── qa_service.py
    └── retriever.py
```

## Environment

在项目根目录 `.env` 中增加：

```text
LLM_PROVIDER=aliyun-bailian
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_TIMEOUT=60
LLM_MAX_RETRIES=2
LLM_IGNORE_PROXY=false
```

也可以换成兼容 OpenAI Chat Completions 接口的服务商，只要提供：

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

## Run

先只预览检索结果和 prompt，不调用 API：

```bash
python ai/ask.py "我是应届毕业生，想在厦门创业，有什么补贴？" --dry-run
```

调用大模型：

```bash
python ai/ask.py "我是应届毕业生，想在厦门创业，有什么补贴？"
```

如果遇到 `SSL handshake failed`、`UNEXPECTED_EOF_WHILE_READING` 或代理连接错误，通常是本机代理/TLS 链路问题。可以先确认代理规则允许访问：

```bash
curl -I https://dashscope.aliyuncs.com
```

如果你想临时让 AI 请求不读取系统代理，可以在 `.env` 中设置：

```text
LLM_IGNORE_PROXY=true
```

## Notes

当前检索是基于 MySQL 关键词匹配，不是向量检索。后续可以继续增加：

```text
policy_chunk
embedding
向量数据库
qa_record / qa_reference 自动保存
```
