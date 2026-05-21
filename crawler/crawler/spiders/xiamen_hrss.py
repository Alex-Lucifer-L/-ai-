"""Spider for Xiamen HRSS public policy pages."""

from dataclasses import dataclass
import logging
import re
import time
from typing import Iterable, Iterator, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from crawler.models import PolicyDocument, PolicyLink
from crawler.utils import DEFAULT_HEADERS, clean_text, make_summary, parse_date


BASE_URL = "https://hrss.xm.gov.cn"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class HrssListSource:
    name: str
    url: str


DEFAULT_SOURCES = (
    HrssListSource(
        "就业创业",
        "https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/qtxx/jycy/",
    ),
    HrssListSource(
        "人才服务",
        "https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/qtxx/rcfw/",
    ),
    HrssListSource(
        "规范性文件",
        "https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/zcfg/gfxwj/",
    ),
    HrssListSource(
        "其他政策文件",
        "https://hrss.xm.gov.cn/xxgk/zfxxgkzl/zfxxgkml/zcfg/qtwj/",
    ),
    HrssListSource("通知公告", "https://hrss.xm.gov.cn/xxgk/tzgg/"),
)

STATIC_DOCUMENT_LINKS = (
    PolicyLink(
        title="入厦政策",
        url="https://app.hrss.xm.gov.cn/ggfwwt-auth/zdcypt/intoyhzc",
        source_name="入厦政策专题",
    ),
    PolicyLink(
        title="毕业生入厦政策指南",
        url="https://app.hrss.xm.gov.cn/ggfwwt-auth/mnhr/intograduate",
        source_name="毕业生入厦政策专题",
    ),
    PolicyLink(
        title="优秀毕业生入厦政策",
        url="https://app.hrss.xm.gov.cn/ggfwwt-auth/yxbyszt/intorxzc",
        source_name="优秀毕业生入厦专题",
    ),
)

RELEVANT_KEYWORDS = (
    "高校毕业生",
    "毕业生",
    "就业",
    "创业",
    "补贴",
    "见习",
    "培训",
    "人才",
    "生活补贴",
    "住房补贴",
    "社保补贴",
    "求职",
    "落户",
    "入厦",
)


class XiamenHrssSpider:
    def __init__(self, timeout: int = 15, delay_seconds: float = 1):
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update(DEFAULT_HEADERS)

    def crawl(
        self,
        sources: Iterable[HrssListSource] = DEFAULT_SOURCES,
        static_links: Iterable[PolicyLink] = STATIC_DOCUMENT_LINKS,
        max_pages: int = 1,
        max_items: int = 20,
        include_static: bool = True,
        relevant_only: bool = False,
    ) -> Iterator[PolicyDocument]:
        seen_urls: set[str] = set()
        count = 0

        if include_static:
            for link in static_links:
                document = self._parse_link_safely(link)
                if document is None:
                    continue
                if relevant_only and not self._is_relevant(document):
                    continue
                seen_urls.add(link.url)
                yield document
                count += 1
                if count >= max_items:
                    return
                time.sleep(self.delay_seconds)

        for source in sources:
            for list_url in self._list_page_urls(source.url, max_pages):
                try:
                    links = self.parse_list_page(list_url, source.name)
                except requests.RequestException as exc:
                    LOGGER.warning("Failed to fetch list page %s: %s", list_url, exc)
                    continue

                for link in links:
                    if link.url in seen_urls:
                        continue
                    seen_urls.add(link.url)

                    document = self._parse_link_safely(link)
                    if document is None:
                        continue
                    if relevant_only and not self._is_relevant(document):
                        continue

                    yield document
                    count += 1
                    if count >= max_items:
                        return
                    time.sleep(self.delay_seconds)

    def parse_list_page(self, url: str, source_name: str) -> list[PolicyLink]:
        html = self._get_text(url)
        soup = BeautifulSoup(html, "lxml")
        links_by_url: dict[str, PolicyLink] = {}

        for anchor in soup.select("a[href]"):
            title = clean_text(anchor.get_text(" "))
            href = anchor.get("href", "").strip()
            if not title or not href:
                continue

            detail_url = urljoin(url, href)
            if not self._is_hrss_detail_url(detail_url):
                continue

            parent_text = clean_text(anchor.parent.get_text(" ")) if anchor.parent else title
            publish_date = parse_date(parent_text)
            link = PolicyLink(
                title=title,
                url=detail_url,
                publish_date=publish_date,
                source_name=source_name,
            )
            existing = links_by_url.get(detail_url)
            if existing is None or len(link.title) > len(existing.title):
                links_by_url[detail_url] = link

        return list(links_by_url.values())

    def parse_detail_page(self, link: PolicyLink) -> Optional[PolicyDocument]:
        html = self._get_text(link.url)
        soup = BeautifulSoup(html, "lxml")

        title = link.title if link.source_name.endswith("专题") else self._extract_title(soup)
        title = title or link.title
        full_text = self._extract_article_text(soup)
        if not full_text:
            return None

        policy_number = self._extract_policy_number(full_text)
        publish_date = link.publish_date or self._extract_publish_date(soup, full_text)
        issuing_department = self._extract_issuing_department(title, full_text)

        return PolicyDocument(
            title=title,
            policy_number=policy_number,
            issuing_department=issuing_department,
            publish_level="city",
            publish_date=publish_date,
            status="effective",
            source_url=link.url,
            full_text=full_text,
            summary=make_summary(full_text),
        )

    def _get_text(self, url: str) -> str:
        urls = [url]
        if url.startswith("https://"):
            urls.append(f"http://{url.removeprefix('https://')}")

        last_error: Optional[requests.RequestException] = None
        for candidate_url in urls:
            try:
                response = self.session.get(candidate_url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or response.encoding
                return response.text
            except requests.RequestException as exc:
                last_error = exc
                LOGGER.debug("Fetch failed for %s: %s", candidate_url, exc)

        if last_error:
            raise last_error
        raise RuntimeError(f"Unable to fetch {url}")

    def _parse_link_safely(self, link: PolicyLink) -> Optional[PolicyDocument]:
        try:
            return self.parse_detail_page(link)
        except requests.RequestException as exc:
            LOGGER.warning("Failed to fetch detail page %s: %s", link.url, exc)
            return None

    def _is_relevant(self, document: PolicyDocument) -> bool:
        text = f"{document.title}\n{document.full_text}"
        return any(keyword in text for keyword in RELEVANT_KEYWORDS)

    def _list_page_urls(self, start_url: str, max_pages: int) -> Iterator[str]:
        yield start_url
        if max_pages <= 1:
            return

        for page_no in range(1, max_pages):
            yield urljoin(start_url, f"index_{page_no}.htm")

    def _is_hrss_detail_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc and parsed.netloc != "hrss.xm.gov.cn":
            return False
        return bool(re.search(r"/t\d+_\d+\.htm$", parsed.path))

    def _extract_title(self, soup: BeautifulSoup) -> str:
        selectors = ("h1", ".article-title", ".title", "meta[name='ArticleTitle']")
        for selector in selectors:
            element = soup.select_one(selector)
            if not element:
                continue
            if element.name == "meta":
                title = element.get("content", "")
            else:
                title = element.get_text(" ")
            title = clean_text(title)
            if title:
                return title

        if soup.title and soup.title.string:
            return clean_text(soup.title.string.split("-")[0])
        return ""

    def _extract_article_text(self, soup: BeautifulSoup) -> str:
        selectors = (
            ".TRS_Editor",
            ".article-content",
            ".article",
            ".content",
            "#zoom",
            "#article",
        )
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = self._clean_article_text(element.get_text("\n"))
                if len(text) >= 80:
                    return text

        candidates = soup.find_all(["article", "main", "div", "td"])
        best_text = ""
        for element in candidates:
            text = self._clean_article_text(element.get_text("\n"))
            if len(text) > len(best_text):
                best_text = text
        return best_text

    def _clean_article_text(self, text: str) -> str:
        text = clean_text(text)
        stop_markers = (
            "微信 微博 QQ空间",
            "快速通道：",
            "联系我们",
            "网站标识码",
            "版权所有：",
            "主办：",
        )
        for marker in stop_markers:
            if marker in text:
                text = text.split(marker, 1)[0]
        return clean_text(text)

    def _extract_policy_number(self, text: str) -> Optional[str]:
        match = re.search(r"[\u4e00-\u9fa5]{1,8}〔\d{4}〕\d+号", text)
        return match.group(0) if match else None

    def _extract_publish_date(self, soup: BeautifulSoup, text: str):
        meta_selectors = (
            "meta[name='PubDate']",
            "meta[name='publishdate']",
            "meta[name='ContentSource']",
        )
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element:
                parsed = parse_date(element.get("content", ""))
                if parsed:
                    return parsed

        matches = re.findall(r"\d{4}[-年/]\d{1,2}[-月/]\d{1,2}日?", text[:1000])
        for value in matches:
            parsed = parse_date(value)
            if parsed:
                return parsed
        return None

    def _extract_issuing_department(self, title: str, text: str) -> str:
        known_departments = (
            "厦门市人力资源和社会保障局",
            "厦门市财政局",
            "厦门市人民政府办公厅",
            "厦门市人民政府",
        )
        matched = [name for name in known_departments if name in title or name in text[:500]]
        if matched:
            return " ".join(dict.fromkeys(matched))
        return "厦门市人力资源和社会保障局"


def crawl_policy_documents(
    max_pages: int = 1,
    max_items: int = 20,
    timeout: int = 15,
    delay_seconds: float = 1,
    relevant_only: bool = False,
) -> Iterable[PolicyDocument]:
    spider = XiamenHrssSpider(timeout=timeout, delay_seconds=delay_seconds)
    return spider.crawl(
        max_pages=max_pages,
        max_items=max_items,
        relevant_only=relevant_only,
    )
