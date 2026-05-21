"""Q&A service orchestration."""

from dataclasses import asdict

from ai.config import AIConfig
from ai.llm_client import LLMClient
from ai.prompt_builder import build_prompt, render_prompt
from ai.retriever import PolicyRetriever


class QAService:
    def __init__(self, config: AIConfig):
        self.retriever = PolicyRetriever(config.database)
        self.llm = LLMClient(config.llm)

    def answer(self, question: str, top_k: int = 5, dry_run: bool = False) -> str:
        result = self.answer_with_references(question, top_k=top_k, dry_run=dry_run)
        return result["answer"]

    def answer_with_references(
        self, question: str, top_k: int = 5, dry_run: bool = False
    ) -> dict[str, object]:
        references = self.retriever.search(question, top_k=top_k)
        messages = build_prompt(question, references)

        if dry_run:
            lines = ["# Retrieved References"]
            for index, reference in enumerate(references, start=1):
                lines.append(
                    f"[{index}] item#{reference.item_id} {reference.item_name} "
                    f"({reference.category_name}, {reference.regions or '未标明地区'})"
                )
                lines.append(f"    {reference.source_url}")
            lines.append("\n# Prompt")
            lines.append(render_prompt(messages))
            answer = "\n".join(lines)
        else:
            answer = self.llm.chat(messages)

        return {
            "answer": answer,
            "references": [asdict(reference) for reference in references],
        }
