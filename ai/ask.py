"""Command line entry point for policy AI Q&A."""

import argparse
import sys

from ai.config import load_ai_config
from ai.qa_service import QAService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ask policy questions with retrieved context.")
    parser.add_argument("question", help="User question, wrapped in quotes.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of policy items to retrieve.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show retrieved references and prompt. Do not call the LLM API.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_ai_config()
    service = QAService(config)
    result = service.answer(args.question, top_k=args.top_k, dry_run=args.dry_run)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
