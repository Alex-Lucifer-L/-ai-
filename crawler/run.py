"""Crawler entry point."""

import argparse
import logging

from crawler.config import load_config
from crawler.db import PolicyDocumentRepository
from crawler.spiders.xiamen_hrss import XiamenHrssSpider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl official policy documents.")
    parser.add_argument(
        "--source",
        choices=("xiamen-hrss",),
        default="xiamen-hrss",
        help="Official source to crawl.",
    )
    parser.add_argument("--max-pages", type=int, default=1, help="List pages per source.")
    parser.add_argument("--max-items", type=int, default=10, help="Maximum documents.")
    parser.add_argument(
        "--skip-static",
        action="store_true",
        help="Skip manually selected topic pages and only crawl list pages.",
    )
    parser.add_argument(
        "--relevant-only",
        action="store_true",
        help="Keep only documents containing employment, graduate, subsidy, talent, training, or settlement keywords.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save crawled documents to MySQL. Without this flag, only preview results.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show crawler warnings.")
    return parser


def main():
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    config = load_config()

    if args.source == "xiamen-hrss":
        spider = XiamenHrssSpider(
            timeout=config.request_timeout,
            delay_seconds=config.crawl_delay_seconds,
        )
        documents = spider.crawl(
            max_pages=args.max_pages,
            max_items=args.max_items,
            include_static=not args.skip_static,
            relevant_only=args.relevant_only,
        )
    else:
        raise ValueError(f"Unsupported source: {args.source}")

    repository = PolicyDocumentRepository(config.database) if args.save else None

    total = 0
    for document in documents:
        total += 1
        if repository:
            document_id = repository.insert_if_not_exists(document)
            print(f"[saved] #{document_id} {document.title}")
        else:
            print(f"[preview] {document.publish_date} {document.title}")
            print(f"          {document.source_url}")

    action = "Saved" if args.save else "Previewed"
    print(f"{action} {total} document(s).")


if __name__ == "__main__":
    main()
