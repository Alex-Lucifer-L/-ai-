# Web

本目录是本地网页前端，用于把已有的 AI 问答模块做成浏览器界面。

## Run

在项目根目录运行：

```bash
python web/app.py
```

然后打开：

```text
http://127.0.0.1:7860
```

如需换端口：

```bash
python web/app.py --port 7870
```

## Features

```text
输入政策问题
选择引用条数
可切换“只看检索”
调用 ai/ai/qa_service.py
展示 AI 回答
展示数据库检索到的 policy_item 引用依据
```

## Notes

网页后端复用项目根目录 `.env` 中的数据库和大模型配置。

如果网页返回 SSL 或代理错误，说明问题发生在大模型 API 网络请求阶段，不是前端页面本身的问题。
