"""Generic spiders for additional official policy sources."""

from dataclasses import dataclass
import json
import logging
import re
import time
from typing import Iterable, Iterator, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from crawler.models import PolicyDocument, PolicyLink
from crawler.utils import DEFAULT_HEADERS, clean_text, make_summary, parse_date


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class OfficialSource:
    group: str
    name: str
    url: str
    source_type: str
    publish_level: str
    issuing_department: str
    allowed_domain: str


OFFICIAL_SOURCES = (
    OfficialSource(
        group="fujian-hrss",
        name="福建省高校毕业生就业创业扶持政策",
        url="https://rst.fujian.gov.cn/zw/ldjy/201906/t20190614_4900105.htm",
        source_type="static",
        publish_level="province",
        issuing_department="福建省人力资源和社会保障厅",
        allowed_domain="rst.fujian.gov.cn",
    ),
    OfficialSource(
        group="fujian-hrss",
        name="福建省就业创业政策清单",
        url="https://rst.fujian.gov.cn/zw/ldjy/201911/t20191129_5141912.htm",
        source_type="static",
        publish_level="province",
        issuing_department="福建省人力资源和社会保障厅",
        allowed_domain="rst.fujian.gov.cn",
    ),
    OfficialSource(
        group="fujian-hrss",
        name="福建省进一步促进高校毕业生自主创业八条措施",
        url="https://rst.fujian.gov.cn/zw/zxwj/bbmwj/202109/t20210914_5688447.htm",
        source_type="static",
        publish_level="province",
        issuing_department="福建省人力资源和社会保障厅",
        allowed_domain="rst.fujian.gov.cn",
    ),
    OfficialSource(
        group="fujian-hrss",
        name="福建省做好2025年高校毕业生等青年就业创业工作的通知",
        url="https://rst.fujian.gov.cn/zw/zfxxgk/zfxxgkml/zyywgz/jycj/202506/t20250618_6928834.htm",
        source_type="static",
        publish_level="province",
        issuing_department="福建省人力资源和社会保障厅",
        allowed_domain="rst.fujian.gov.cn",
    ),
    OfficialSource(
        group="fujian-hrss",
        name="福建省人社厅-毕业生就业创业问答",
        url="https://rst.fujian.gov.cn/wz/cjwt/bysjycy/bysjydj/",
        source_type="list",
        publish_level="province",
        issuing_department="福建省人力资源和社会保障厅",
        allowed_domain="rst.fujian.gov.cn",
    ),
    OfficialSource(
        group="xiamen-gov",
        name="厦门市政府-稳岗就业",
        url="https://www.xm.gov.cn/zdxxgk/jycy/",
        source_type="list",
        publish_level="city",
        issuing_department="厦门市人民政府",
        allowed_domain="www.xm.gov.cn",
    ),
    OfficialSource(
        group="xiamen-gov",
        name="厦门市政府-人才补贴服务",
        url="https://www.xm.gov.cn/wsbs/ztfw/fwcj/jycy/rcbtfw/",
        source_type="static",
        publish_level="city",
        issuing_department="厦门市人民政府",
        allowed_domain="www.xm.gov.cn",
    ),
    OfficialSource(
        group="xiamen-gov",
        name="厦门市政府-技能提升补贴服务",
        url="https://www.xm.gov.cn/wsbs/ztfw/fwcj/jycy/jntsbtfw/",
        source_type="static",
        publish_level="city",
        issuing_department="厦门市人民政府",
        allowed_domain="www.xm.gov.cn",
    ),
    OfficialSource(
        group="xiamen-gov",
        name="厦门市政府-灵活就业参保服务",
        url="https://www.xm.gov.cn/wsbs/ztfw/fwcj/jycy/lhjycbfw/",
        source_type="static",
        publish_level="city",
        issuing_department="厦门市人民政府",
        allowed_domain="www.xm.gov.cn",
    ),
    OfficialSource(
        group="district-gov",
        name="集美区政府-创业资金申请",
        url="https://www.jimei.gov.cn/nrrh/202309/t20230926_937426.htm",
        source_type="static",
        publish_level="district",
        issuing_department="厦门市集美区人民政府",
        allowed_domain="www.jimei.gov.cn",
    ),
    OfficialSource(
        group="district-gov",
        name="海沧区政府-就业创业",
        url="https://www.haicang.gov.cn/xx/zdxxgk/zdxxgk/jycy/",
        source_type="list",
        publish_level="district",
        issuing_department="厦门市海沧区人民政府",
        allowed_domain="www.haicang.gov.cn",
    ),
    OfficialSource(
        group="district-gov",
        name="海沧区政府-毕业生就业创业补贴",
        url="https://www.haicang.gov.cn/xx/ywdt/hcyw/jrhc/202507/t20250716_1108574.htm",
        source_type="static",
        publish_level="district",
        issuing_department="厦门市海沧区人民政府",
        allowed_domain="www.haicang.gov.cn",
    ),
    OfficialSource(
        group="district-gov",
        name="思明区政府-重点群体项目制培训",
        url="https://www.siming.gov.cn/xxgk/zwgkzdgz/wgjy/jyzc/202303/t20230306_901057.htm",
        source_type="static",
        publish_level="district",
        issuing_department="厦门市思明区人民政府",
        allowed_domain="www.siming.gov.cn",
    ),
    OfficialSource(
        group="district-gov",
        name="湖里区政府-人才及重点群体住房保障",
        url="https://www.huli.gov.cn/nrrh/202312/t20231202_1027800.htm",
        source_type="static",
        publish_level="district",
        issuing_department="厦门市湖里区人民政府",
        allowed_domain="www.huli.gov.cn",
    ),
)


class OfficialGenericSpider:
    def __init__(self, timeout: int = 15, delay_seconds: float = 1):
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update(DEFAULT_HEADERS)

    def crawl(
        self,
        groups: Iterable[str] = ("fujian-hrss", "xiamen-gov", "district-gov"),
        max_pages: int = 1,
        max_items: int = 20,
        relevant_only: bool = False,
    ) -> Iterator[PolicyDocument]:
        selected_groups = set(groups)
        seen_urls: set[str] = set()
        count = 0

        for source in OFFICIAL_SOURCES:
            if source.group not in selected_groups:
                continue

            for document in self._crawl_source(source, max_pages=max_pages):
                if document.source_url in seen_urls:
                    continue
                seen_urls.add(document.source_url)

                if relevant_only and not self._is_relevant(document):
                    continue

                yield document
                count += 1
                if count >= max_items:
                    return
                time.sleep(self.delay_seconds)

    def _crawl_source(self, source: OfficialSource, max_pages: int) -> Iterator[PolicyDocument]:
        try:
            if source.source_type == "static":
                document = self.parse_detail_page(
                    PolicyLink(title=source.name, url=source.url, source_name=source.name),
                    source,
                )
                if document:
                    yield document
            elif source.source_type == "list":
                for list_url in self._list_page_urls(source.url, max_pages):
                    for link in self.parse_list_page(list_url, source):
                        document = self.parse_detail_page(link, source)
                        if document:
                            yield document
            else:
                raise ValueError(f"Unsupported source type: {source.source_type}")
        except requests.RequestException as exc:
            LOGGER.warning("Failed to crawl source %s: %s", source.name, exc)
        except json.JSONDecodeError as exc:
            LOGGER.warning("Failed to parse JSON source %s: %s", source.name, exc)

    def parse_list_page(self, url: str, source: OfficialSource) -> list[PolicyLink]:
        html = self._get_text(url)
        soup = BeautifulSoup(html, "lxml")
        links_by_url: dict[str, PolicyLink] = {}

        for anchor in soup.select("a[href]"):
            title = clean_text(anchor.get_text(" "))
            href = anchor.get("href", "").strip()
            if not title or not href:
                continue

            detail_url = urljoin(url, href)
            if not self._is_detail_url(detail_url, source.allowed_domain):
                continue

            parent_text = clean_text(anchor.parent.get_text(" ")) if anchor.parent else title
            link = PolicyLink(
                title=title,
                url=detail_url,
                publish_date=parse_date(parent_text),
                source_name=source.name,
            )
            existing = links_by_url.get(detail_url)
            if existing is None or len(link.title) > len(existing.title):
                links_by_url[detail_url] = link

        return list(links_by_url.values())

    def parse_detail_page(self, link: PolicyLink, source: OfficialSource) -> Optional[PolicyDocument]:
        html = self._get_text(link.url)
        soup = BeautifulSoup(html, "lxml")

        title = link.title if source.source_type == "static" else self._extract_title(soup)
        title = title or link.title
        if title in ("厦门市海沧区人民政府", "厦门市人民政府门户网站") and link.title:
            title = link.title
        full_text = self._extract_article_text(soup)
        if not full_text:
            return None

        return PolicyDocument(
            title=title,
            policy_number=self._extract_policy_number(full_text),
            issuing_department=self._extract_issuing_department(title, full_text, source),
            publish_level=source.publish_level,
            publish_date=link.publish_date or self._extract_publish_date(soup, full_text),
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

    def _list_page_urls(self, start_url: str, max_pages: int) -> Iterator[str]:
        yield start_url
        if max_pages <= 1:
            return

        for page_no in range(1, max_pages):
            yield urljoin(start_url, f"index_{page_no}.htm")

    def _is_detail_url(self, url: str, allowed_domain: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc and parsed.netloc != allowed_domain:
            return False
        if url.lower().endswith(".pdf"):
            return False
        return bool(re.search(r"/t\d+_\d+\.html?$", parsed.path))

    def _extract_title(self, soup: BeautifulSoup) -> str:
        selectors = ("h1", ".article-title", ".title", "meta[name='ArticleTitle']")
        for selector in selectors:
            element = soup.select_one(selector)
            if not element:
                continue
            title = element.get("content", "") if element.name == "meta" else element.get_text(" ")
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
            ".mainContent",
            ".detail",
            "#zoom",
            "#article",
            "main",
        )
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = self._clean_article_text(element.get_text("\n"))
                if len(text) >= 80:
                    return text

        best_text = ""
        for element in soup.find_all(["article", "main", "div", "td"]):
            text = self._clean_article_text(element.get_text("\n"))
            if len(text) > len(best_text):
                best_text = text
        return best_text

    def _clean_article_text(self, text: str) -> str:
        text = clean_text(text)
        stop_markers = (
            "微信 微博 QQ空间",
            "扫一扫在手机上查看当前页面",
            "附件下载",
            "相关链接",
            "网站标识码",
            "版权所有",
            "主办：",
        )
        for marker in stop_markers:
            if marker in text:
                text = text.split(marker, 1)[0]
        return clean_text(text)

    def _extract_policy_number(self, text: str) -> Optional[str]:
        match = re.search(r"[\u4e00-\u9fa5]{1,10}[〔\[]\d{4}[〕\]]\d+号", text)
        return match.group(0) if match else None

    def _extract_publish_date(self, soup: BeautifulSoup, text: str):
        for selector in ("meta[name='PubDate']", "meta[name='publishdate']", "meta[name='date']"):
            element = soup.select_one(selector)
            if element:
                parsed = parse_date(element.get("content", ""))
                if parsed:
                    return parsed

        for value in re.findall(r"\d{4}[-年/]\d{1,2}[-月/]\d{1,2}日?", text[:1200]):
            parsed = parse_date(value)
            if parsed:
                return parsed
        return None

    def _extract_issuing_department(self, title: str, text: str, source: OfficialSource) -> str:
        known = (
            source.issuing_department,
            "福建省人力资源和社会保障厅",
            "厦门市人民政府",
            "厦门市人力资源和社会保障局",
            "厦门市教育局",
        )
        matched = [name for name in known if name and (name in title or name in text[:800])]
        if matched:
            return " ".join(dict.fromkeys(matched))
        return source.issuing_department

    def _is_relevant(self, document: PolicyDocument) -> bool:
        text = f"{document.title}\n{document.full_text}"
        keywords = (
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
        return any(keyword in text for keyword in keywords)
