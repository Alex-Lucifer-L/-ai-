"""Shared HTML parsing helpers."""

from bs4 import BeautifulSoup

from crawler.utils import clean_text


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def extract_text(selector: str, soup: BeautifulSoup) -> str:
    element = soup.select_one(selector)
    return clean_text(element.get_text("\n")) if element else ""
