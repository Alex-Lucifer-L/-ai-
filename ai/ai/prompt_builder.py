"""Prompt builder for policy Q&A."""

from ai.retriever import PolicyReference


SYSTEM_PROMPT = """你是厦门大学生/高校毕业生就业创业政策 AI 解读助手。
请只根据提供的政策依据回答，不要编造政策。
如果依据不足，请明确说明“当前数据库中没有足够依据”。
回答应当通俗、结构清晰，并提示用户以官方原文和办理窗口要求为准。"""


def build_prompt(question: str, references: list[PolicyReference]) -> list[dict[str, str]]:
    context = "\n\n".join(
        _format_reference(index + 1, reference)
        for index, reference in enumerate(references)
    )

    user_prompt = f"""用户问题：
{question}

政策依据：
{context or '当前没有检索到相关政策依据。'}

请按以下结构回答：
1. 结论
2. 可能适用的政策
3. 申请条件/适用对象
4. 补贴或扶持内容
5. 办理方式或注意事项
6. 引用来源"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def render_prompt(messages: list[dict[str, str]]) -> str:
    return "\n\n".join(f"{message['role'].upper()}:\n{message['content']}" for message in messages)


def _format_reference(index: int, reference: PolicyReference) -> str:
    return f"""[{index}] {reference.item_name}
分类：{reference.category_name}
适用地区：{reference.regions or '未标明'}
适用对象：{reference.target_group_text or '未提取'}
申请条件：{reference.conditions_text or '未提取'}
扶持内容：{reference.support_content or '未提取'}
补贴标准：{reference.subsidy_standard or '未提取'}
办理流程：{reference.application_process or '未提取'}
办理渠道：{reference.application_channel or '未提取'}
来源文件：{reference.source_title}
来源链接：{reference.source_url}
原文片段：{reference.original_excerpt[:500]}"""
