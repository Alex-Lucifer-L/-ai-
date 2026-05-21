"""Rule-based extraction from policy documents to policy items.

This module is intentionally conservative. It extracts candidate policy
measures from titles, bullets, and paragraphs using keywords. The result is
useful as a first draft for `policy_item`, but still needs later review for
high-stakes use.
"""

import re
from typing import Iterable

from crawler.models import PolicyDocument, PolicyItemCandidate
from crawler.extractors.quality_rules import looks_like_noise_item, suggest_category
from crawler.utils import clean_text, compact_spaces


CATEGORY_KEYWORDS = (
    ("创业扶持", ("创业", "创业担保贷款", "创业项目", "创业创新", "创业资助")),
    ("企业吸纳毕业生补贴", ("企业吸纳", "社保补贴", "吸纳高校毕业生")),
    ("实习/见习", ("见习", "实习")),
    ("职业培训", ("培训", "职业技能", "技能竞赛", "技工院校", "技能提升")),
    ("落户/住房相关支持", ("落户", "入厦", "住房", "租房", "公租房", "保障性商品房")),
    ("人才补贴", ("人才", "生活补贴", "安家补贴", "津贴", "博士后", "高层次")),
    ("就业补贴", ("就业", "求职", "毕业生", "奖补", "补助", "补贴")),
)

MEASURE_KEYWORDS = (
    "补贴",
    "补助",
    "奖补",
    "奖励",
    "资助",
    "津贴",
    "贷款",
    "扶持",
    "见习",
    "培训",
    "落户",
    "住房",
    "就业",
    "创业",
)

TARGET_KEYWORDS = ("高校毕业生", "毕业生", "应届", "青年", "人才", "留学人员", "博士后", "企业")
CONDITION_KEYWORDS = ("符合", "条件", "申请", "申报", "在厦", "缴交", "缴纳", "毕业", "年龄")
MATERIAL_KEYWORDS = ("材料", "身份证", "毕业证", "申请表", "证明", "附件")
PROCESS_KEYWORDS = ("流程", "办理", "申报", "申请", "审核", "公示", "发放")
CHANNEL_KEYWORDS = ("平台", "窗口", "网站", "系统", "线上", "线下", "服务大厅", "厦门智慧人社")
SUBSIDY_PATTERN = re.compile(r"(\d+(?:\.\d+)?\s*(?:元|万元|万|%|个月|年)|最高[^，。；\n]{1,30})")
class PolicyItemExtractor:
    def extract(self, document: PolicyDocument, max_items: int = 8) -> list[PolicyItemCandidate]:
        candidates = []
        topic_candidates = self._extract_topic_page_items(document)
        candidates.extend(topic_candidates)

        if len(topic_candidates) < 2:
            candidates.extend(self._extract_paragraph_items(document))

        if not candidates and self._looks_like_measure(document.title):
            candidates.insert(0, self._candidate_from_excerpt(document.title, document.full_text[:1200], document))

        return self._deduplicate([candidate for candidate in candidates if not self._is_noise(candidate)])[
            :max_items
        ]

    def _extract_topic_page_items(self, document: PolicyDocument) -> list[PolicyItemCandidate]:
        lines = self._lines(document.full_text)
        candidates: list[PolicyItemCandidate] = []
        current_title = ""
        current_body: list[str] = []

        for line in lines:
            if self._looks_like_short_heading(line):
                if current_title and current_body:
                    candidates.append(
                        self._candidate_from_excerpt(current_title, "\n".join(current_body), document)
                    )
                current_title = line
                current_body = []
                continue

            if current_title:
                current_body.append(line)

        if current_title and current_body:
            candidates.append(self._candidate_from_excerpt(current_title, "\n".join(current_body), document))

        return [candidate for candidate in candidates if self._is_candidate_relevant(candidate)]

    def _extract_paragraph_items(self, document: PolicyDocument) -> list[PolicyItemCandidate]:
        chunks = self._chunks(document.full_text)
        candidates: list[PolicyItemCandidate] = []

        for chunk in chunks:
            if not self._looks_like_measure(chunk):
                continue

            item_name = self._infer_item_name(chunk, document.title)
            candidates.append(self._candidate_from_excerpt(item_name, chunk, document))

        return candidates

    def _candidate_from_excerpt(
        self,
        item_name: str,
        excerpt: str,
        document: PolicyDocument,
    ) -> PolicyItemCandidate:
        excerpt = clean_text(excerpt)
        item_name = self._normalize_item_name(item_name, document.title)
        category_name = suggest_category(item_name, excerpt, self._classify_category(item_name, excerpt))

        return PolicyItemCandidate(
            item_name=item_name,
            category_name=category_name,
            target_group_text=self._extract_by_keywords(excerpt, TARGET_KEYWORDS),
            conditions_text=self._extract_by_keywords(excerpt, CONDITION_KEYWORDS),
            support_content=self._extract_support_content(excerpt),
            subsidy_standard=self._extract_subsidy_standard(excerpt),
            application_materials=self._extract_by_keywords(excerpt, MATERIAL_KEYWORDS),
            application_process=self._extract_by_keywords(excerpt, PROCESS_KEYWORDS),
            application_channel=self._extract_by_keywords(excerpt, CHANNEL_KEYWORDS),
            keywords=self._keywords_for_text(f"{document.title}\n{item_name}\n{excerpt}"),
            status=document.status,
            original_excerpt=excerpt[:2000],
        )

    def _lines(self, text: str) -> list[str]:
        return [line for line in clean_text(text).splitlines() if line]

    def _chunks(self, text: str) -> list[str]:
        lines = self._lines(text)
        chunks: list[str] = []
        current: list[str] = []

        for line in lines:
            current.append(line)
            if self._ends_chunk(line) or len("".join(current)) >= 350:
                chunks.append("\n".join(current))
                current = []

        if current:
            chunks.append("\n".join(current))
        return chunks

    def _ends_chunk(self, line: str) -> bool:
        return bool(re.match(r"^[一二三四五六七八九十]+[、.．]", line)) or line.endswith("。")

    def _looks_like_short_heading(self, line: str) -> bool:
        if len(line) > 32:
            return False
        if "0592" in line or re.search(r"\d{4,}", line):
            return False
        if any(keyword in line for keyword in MEASURE_KEYWORDS):
            return True
        return bool(re.match(r"^[一二三四五六七八九十]+[、.．]", line))

    def _looks_like_measure(self, text: str) -> bool:
        return any(keyword in text for keyword in MEASURE_KEYWORDS)

    def _is_candidate_relevant(self, candidate: PolicyItemCandidate) -> bool:
        text = f"{candidate.item_name}\n{candidate.original_excerpt or ''}"
        return self._looks_like_measure(text)

    def _is_noise(self, candidate: PolicyItemCandidate) -> bool:
        decision = looks_like_noise_item(candidate.item_name, candidate.original_excerpt or "")
        if decision.is_noise:
            return True
        return not candidate.support_content and not candidate.subsidy_standard

    def _normalize_item_name(self, item_name: str, fallback_title: str) -> str:
        item_name = compact_spaces(item_name)
        item_name = re.sub(r"^[★*·•\-\s]+", "", item_name)
        item_name = re.sub(r"^[一二三四五六七八九十]+[、.．]\s*", "", item_name)
        if not item_name:
            item_name = fallback_title
        if len(item_name) > 80:
            item_name = self._infer_item_name(item_name, fallback_title)
        return item_name[:300]

    def _infer_item_name(self, text: str, fallback_title: str) -> str:
        first_sentence = re.split(r"[。；;\n]", compact_spaces(text), maxsplit=1)[0]
        for keyword in MEASURE_KEYWORDS:
            if keyword in first_sentence and len(first_sentence) <= 80:
                return first_sentence
        return fallback_title

    def _classify_category(self, item_name: str, text: str) -> str:
        for category_name, keywords in CATEGORY_KEYWORDS:
            if any(keyword in item_name for keyword in keywords):
                return category_name

        best_category = "就业补贴"
        best_score = 0
        for category_name, keywords in CATEGORY_KEYWORDS:
            score = sum(1 for keyword in keywords if keyword in text)
            if score > best_score:
                best_category = category_name
                best_score = score
        return best_category

    def _extract_by_keywords(self, text: str, keywords: Iterable[str]) -> str | None:
        sentences = self._sentences(text)
        matched = [sentence for sentence in sentences if any(keyword in sentence for keyword in keywords)]
        return "\n".join(matched[:4]) or None

    def _extract_support_content(self, text: str) -> str | None:
        return self._extract_by_keywords(text, MEASURE_KEYWORDS) or compact_spaces(text)[:500]

    def _extract_subsidy_standard(self, text: str) -> str | None:
        sentences = self._sentences(text)
        matched = [
            sentence
            for sentence in sentences
            if ("补贴" in sentence or "补助" in sentence or "奖补" in sentence or "资助" in sentence)
            and SUBSIDY_PATTERN.search(sentence)
        ]
        if matched:
            return "\n".join(matched[:4])

        loose_matches = SUBSIDY_PATTERN.findall(text)
        if loose_matches:
            return "；".join(dict.fromkeys(match.strip() for match in loose_matches[:8]))
        return None

    def _sentences(self, text: str) -> list[str]:
        text = compact_spaces(text)
        sentences = re.split(r"(?<=[。；;])", text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _keywords_for_text(self, text: str) -> str:
        keywords = [keyword for keyword in MEASURE_KEYWORDS + TARGET_KEYWORDS if keyword in text]
        return " ".join(dict.fromkeys(keywords))

    def _deduplicate(self, candidates: list[PolicyItemCandidate]) -> list[PolicyItemCandidate]:
        result: list[PolicyItemCandidate] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = compact_spaces(candidate.item_name)
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate)
        return result
