"""Data models used by the crawler."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class PolicyDocument:
    title: str
    issuing_department: str
    publish_level: str
    source_url: str
    full_text: str
    policy_number: Optional[str] = None
    publish_date: Optional[date] = None
    summary: Optional[str] = None
    status: str = "effective"


@dataclass(frozen=True)
class PolicyLink:
    title: str
    url: str
    publish_date: Optional[date] = None
    source_name: str = ""
