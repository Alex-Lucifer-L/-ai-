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
    document_id: Optional[int] = None


@dataclass(frozen=True)
class PolicyLink:
    title: str
    url: str
    publish_date: Optional[date] = None
    source_name: str = ""


@dataclass(frozen=True)
class PolicyItemCandidate:
    item_name: str
    category_name: str
    target_group_text: Optional[str] = None
    conditions_text: Optional[str] = None
    support_content: Optional[str] = None
    subsidy_standard: Optional[str] = None
    application_materials: Optional[str] = None
    application_process: Optional[str] = None
    application_channel: Optional[str] = None
    keywords: Optional[str] = None
    status: str = "effective"
    original_excerpt: Optional[str] = None


@dataclass(frozen=True)
class StoredPolicyItem:
    item_id: int
    document_id: int
    item_name: str
    category_name: str
    publish_level: Optional[str]
    text: str
    status: str = "effective"
