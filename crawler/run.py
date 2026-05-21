"""Crawler entry point."""

import argparse
import logging

from crawler.config import load_config
from crawler.db import PolicyDocumentRepository
from crawler.extractors.policy_item_extractor import PolicyItemExtractor
from crawler.extractors.quality_rules import looks_like_noise_item, suggest_category
from crawler.extractors.region_matcher import RegionMatcher
from crawler.models import PolicyDocument, PolicyItemCandidate
from crawler.spiders.official_generic import OfficialGenericSpider
from crawler.spiders.xiamen_hrss import XiamenHrssSpider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl official policy documents.")
    parser.add_argument(
        "--source",
        choices=("xiamen-hrss", "fujian-hrss", "xiamen-gov", "district-gov", "official-sites"),
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
    parser.add_argument(
        "--extract-items",
        action="store_true",
        help="Extract policy_item candidates from crawled or loaded policy documents.",
    )
    parser.add_argument(
        "--extract-from-db",
        action="store_true",
        help="Load existing policy_document rows from MySQL and extract policy_item candidates.",
    )
    parser.add_argument(
        "--document-id",
        type=int,
        default=None,
        help="When using --extract-from-db, extract only one policy_document row.",
    )
    parser.add_argument(
        "--backfill-regions",
        action="store_true",
        help="Preview or save item_region matches for existing policy_item rows.",
    )
    parser.add_argument(
        "--item-id",
        type=int,
        default=None,
        help="When using --backfill-regions, process only one policy_item row.",
    )
    parser.add_argument(
        "--include-existing-regions",
        action="store_true",
        help="When using --backfill-regions, include items that already have item_region rows.",
    )
    parser.add_argument(
        "--review-noisy-items",
        action="store_true",
        help="Preview likely noisy policy_item rows. With --save, mark them as review_noise.",
    )
    parser.add_argument(
        "--clean-items",
        action="store_true",
        help="Preview or apply quality cleanup: mark noisy items and fix obvious category mismatches.",
    )
    parser.add_argument("--verbose", action="store_true", help="Show crawler warnings.")
    return parser


def print_document_preview(document: PolicyDocument) -> None:
    print(f"[preview] {document.publish_date} {document.title}")
    print(f"          {document.source_url}")


def print_item_preview(item: PolicyItemCandidate) -> None:
    print(f"  [item] {item.category_name} | {item.item_name}")
    if item.subsidy_standard:
        print(f"         标准: {item.subsidy_standard[:120]}")
    if item.target_group_text:
        print(f"         对象: {item.target_group_text[:120]}")


def extract_items_for_document(
    document: PolicyDocument,
    extractor: PolicyItemExtractor,
    repository: PolicyDocumentRepository | None,
    save: bool,
    document_id: int | None,
) -> int:
    items = extractor.extract(document)
    for item in items:
        if save and repository and document_id is not None:
            item_id = repository.insert_policy_item_for_document(document_id, item)
            print(f"  [saved-item] #{item_id} {item.category_name} | {item.item_name}")
        else:
            print_item_preview(item)
    return len(items)


def looks_like_noisy_stored_item(item_name: str, text: str) -> bool:
    return looks_like_noise_item(item_name, text).is_noise


def backfill_regions(
    repository: PolicyDocumentRepository,
    limit: int,
    item_id: int | None,
    include_existing: bool,
    save: bool,
) -> None:
    matcher = RegionMatcher()
    items = repository.list_policy_items_for_region_backfill(
        limit=limit,
        item_id=item_id,
        include_existing=include_existing,
    )

    total_matches = 0
    for item in items:
        matches = matcher.match(item.text, publish_level=item.publish_level)
        if not matches:
            print(f"[region-skip] #{item.item_id} {item.item_name}")
            continue

        for match in matches:
            total_matches += 1
            if save:
                inserted = repository.insert_item_region_if_not_exists(item.item_id, match)
                action = "saved-region" if inserted else "existing-region"
            else:
                action = "preview-region"
            print(f"[{action}] item#{item.item_id} {item.item_name} -> {match.region_name}")

    action = "Saved" if save else "Previewed"
    print(f"{action} {total_matches} item_region match(es).")


def review_noisy_items(
    repository: PolicyDocumentRepository,
    limit: int,
    item_id: int | None,
    save: bool,
) -> None:
    items = repository.list_policy_items_for_region_backfill(
        limit=limit,
        item_id=item_id,
        include_existing=True,
    )
    noisy_ids = [
        item.item_id
        for item in items
        if looks_like_noisy_stored_item(item.item_name, item.text)
    ]

    for item in items:
        if item.item_id in noisy_ids:
            print(f"[noise] #{item.item_id} {item.category_name} | {item.item_name}")

    if save:
        updated = repository.mark_policy_items_review_noise(noisy_ids)
        print(f"Marked {updated} policy_item row(s) as review_noise.")
    else:
        print(f"Found {len(noisy_ids)} likely noisy policy_item row(s).")


def clean_items(
    repository: PolicyDocumentRepository,
    limit: int,
    item_id: int | None,
    save: bool,
) -> None:
    items = repository.list_policy_items_for_quality_review(
        limit=limit,
        item_id=item_id,
        include_noise=False,
    )
    noisy_ids: list[int] = []
    category_updates: list[tuple[int, str, str, str]] = []

    for item in items:
        noise_decision = looks_like_noise_item(item.item_name, item.text)
        if noise_decision.is_noise:
            noisy_ids.append(item.item_id)
            print(f"[clean-noise] #{item.item_id} {item.category_name} | {item.item_name} | {noise_decision.reason}")
            continue

        suggested_category = suggest_category(
            item.item_name,
            item.text,
            item.category_name,
            conservative=True,
        )
        if suggested_category != item.category_name:
            category_updates.append(
                (item.item_id, item.category_name, suggested_category, item.item_name)
            )
            print(
                f"[clean-category] #{item.item_id} {item.category_name} -> {suggested_category} | {item.item_name}"
            )

    if save:
        marked = repository.mark_policy_items_review_noise(noisy_ids)
        updated = 0
        for item_id_value, _old_category, new_category, _item_name in category_updates:
            if repository.update_policy_item_category(item_id_value, new_category):
                updated += 1
        print(f"Marked {marked} noisy item(s).")
        print(f"Updated {updated} category value(s).")
    else:
        print(f"Found {len(noisy_ids)} noisy item(s).")
        print(f"Found {len(category_updates)} category update candidate(s).")


def main():
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    config = load_config()
    repository = (
        PolicyDocumentRepository(config.database)
        if args.save
        or args.extract_from_db
        or args.backfill_regions
        or args.review_noisy_items
        or args.clean_items
        else None
    )
    extractor = PolicyItemExtractor() if args.extract_items or args.extract_from_db else None

    if args.backfill_regions:
        if repository is None:
            raise RuntimeError("Database repository is required for --backfill-regions.")
        backfill_regions(
            repository=repository,
            limit=args.max_items,
            item_id=args.item_id,
            include_existing=args.include_existing_regions,
            save=args.save,
        )
        return

    if args.review_noisy_items:
        if repository is None:
            raise RuntimeError("Database repository is required for --review-noisy-items.")
        review_noisy_items(
            repository=repository,
            limit=args.max_items,
            item_id=args.item_id,
            save=args.save,
        )
        return

    if args.clean_items:
        if repository is None:
            raise RuntimeError("Database repository is required for --clean-items.")
        clean_items(
            repository=repository,
            limit=args.max_items,
            item_id=args.item_id,
            save=args.save,
        )
        return

    if args.extract_from_db:
        if repository is None:
            raise RuntimeError("Database repository is required for --extract-from-db.")
        documents = repository.list_documents(
            limit=args.max_items,
            document_id=args.document_id,
        )
    elif args.source == "xiamen-hrss":
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
    elif args.source in {"fujian-hrss", "xiamen-gov", "district-gov", "official-sites"}:
        spider = OfficialGenericSpider(
            timeout=config.request_timeout,
            delay_seconds=config.crawl_delay_seconds,
        )
        groups = (
            ("fujian-hrss", "xiamen-gov", "district-gov")
            if args.source == "official-sites"
            else (args.source,)
        )
        documents = spider.crawl(
            groups=groups,
            max_pages=args.max_pages,
            max_items=args.max_items,
            relevant_only=args.relevant_only,
        )
    else:
        raise ValueError(f"Unsupported source: {args.source}")

    total = 0
    total_items = 0
    for document in documents:
        total += 1
        if args.extract_from_db:
            document_id = document.document_id
            print(f"[loaded] #{document_id} {document.title}")
        elif args.save and repository:
            document_id = repository.insert_if_not_exists(document)
            print(f"[saved] #{document_id} {document.title}")
        else:
            document_id = document.document_id
            print_document_preview(document)

        if extractor:
            total_items += extract_items_for_document(
                document=document,
                extractor=extractor,
                repository=repository,
                save=args.save,
                document_id=document_id,
            )

    action = "Saved" if args.save else "Previewed"
    print(f"{action} {total} document(s).")
    if extractor:
        print(f"{action} {total_items} policy item candidate(s).")


if __name__ == "__main__":
    main()
