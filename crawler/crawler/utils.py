"""Common helpers for crawler code."""

from datetime import date, datetime
import re
from typing import Optional


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def parse_date(value: str) -> Optional[date]:
    value = value.strip()
    patterns = (
        (r"\d{4}-\d{1,2}-\d{1,2}", "%Y-%m-%d"),
        (r"\d{4}/\d{1,2}/\d{1,2}", "%Y/%m/%d"),
        (r"\d{4}年\d{1,2}月\d{1,2}日?", "%Y年%m月%d日"),
    )
    for pattern, fmt in patterns:
        match = re.search(pattern, value)
        if not match:
            continue
        date_text = match.group(0)
        if "年" in date_text and not date_text.endswith("日"):
            date_text = f"{date_text}日"
        try:
            return datetime.strptime(date_text, fmt).date()
        except ValueError:
            continue
    return None


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_summary(text: str, max_length: int = 300) -> str:
    summary = compact_spaces(text)
    return summary[:max_length]
