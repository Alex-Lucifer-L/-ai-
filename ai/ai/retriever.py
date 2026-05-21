"""Keyword retriever for policy items."""

from dataclasses import dataclass
import re

import pymysql

from ai.config import DatabaseConfig


@dataclass(frozen=True)
class PolicyReference:
    item_id: int
    item_name: str
    category_name: str
    regions: str
    target_group_text: str
    conditions_text: str
    support_content: str
    subsidy_standard: str
    application_process: str
    application_channel: str
    source_title: str
    source_url: str
    original_excerpt: str


class PolicyRetriever:
    def __init__(self, config: DatabaseConfig):
        self.config = config

    def _connect(self):
        return pymysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def search(self, question: str, top_k: int = 5) -> list[PolicyReference]:
        keywords = self._keywords(question)
        if not keywords:
            keywords = [question]

        where_parts = []
        params: list[object] = []
        searchable_columns = (
            "pi.item_name",
            "c.category_name",
            "pi.target_group_text",
            "pi.conditions_text",
            "pi.support_content",
            "pi.subsidy_standard",
            "pi.keywords",
            "pd.title",
        )

        for keyword in keywords:
            keyword_parts = []
            for column in searchable_columns:
                keyword_parts.append(f"{column} LIKE %s")
                params.append(f"%{keyword}%")
            where_parts.append("(" + " OR ".join(keyword_parts) + ")")

        score_parts = []
        score_params: list[object] = []
        for keyword in keywords:
            score_parts.extend(
                [
                    "CASE WHEN pi.item_name LIKE %s THEN 8 ELSE 0 END",
                    "CASE WHEN pi.subsidy_standard LIKE %s THEN 5 ELSE 0 END",
                    "CASE WHEN pi.support_content LIKE %s THEN 4 ELSE 0 END",
                    "CASE WHEN pi.target_group_text LIKE %s THEN 3 ELSE 0 END",
                    "CASE WHEN pd.title LIKE %s THEN 2 ELSE 0 END",
                ]
            )
            score_params.extend([f"%{keyword}%"] * 5)
        score_sql = " + ".join(score_parts) if score_parts else "0"

        sql = f"""
            SELECT
                pi.item_id,
                pi.item_name,
                c.category_name,
                COALESCE(GROUP_CONCAT(DISTINCT r.region_name ORDER BY r.region_id SEPARATOR '、'), '') AS regions,
                COALESCE(pi.target_group_text, '') AS target_group_text,
                COALESCE(pi.conditions_text, '') AS conditions_text,
                COALESCE(pi.support_content, '') AS support_content,
                COALESCE(pi.subsidy_standard, '') AS subsidy_standard,
                COALESCE(pi.application_process, '') AS application_process,
                COALESCE(pi.application_channel, '') AS application_channel,
                pd.title AS source_title,
                pd.source_url,
                COALESCE(di.original_excerpt, '') AS original_excerpt,
                ({score_sql})
                + CASE WHEN COALESCE(GROUP_CONCAT(DISTINCT r.region_name), '') LIKE %s THEN 3 ELSE 0 END
                + CASE WHEN pi.item_name LIKE %s OR pi.item_name LIKE %s THEN -2 ELSE 0 END
                + CASE WHEN pi.item_name LIKE %s OR pi.item_name LIKE %s THEN -4 ELSE 0 END
                AS relevance_score
            FROM policy_item pi
            JOIN category c ON pi.category_id = c.category_id
            JOIN document_item di ON pi.item_id = di.item_id
            JOIN policy_document pd ON di.document_id = pd.document_id
            LEFT JOIN item_region ir ON pi.item_id = ir.item_id
            LEFT JOIN region r ON ir.region_id = r.region_id
            WHERE pi.status = 'effective'
              AND ({' OR '.join(where_parts)})
            GROUP BY
                pi.item_id,
                pi.item_name,
                c.category_name,
                pi.target_group_text,
                pi.conditions_text,
                pi.support_content,
                pi.subsidy_standard,
                pi.application_process,
                pi.application_channel,
                pd.title,
                pd.source_url,
                di.original_excerpt
            ORDER BY relevance_score DESC, pi.item_id DESC
            LIMIT %s
        """
        ranking_params = ["%厦门%", "%标准%", "%条件%", "%不得%", "%重复%"]
        final_params = score_params + ranking_params + params + [top_k]

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, final_params)
                rows = cursor.fetchall()

        for row in rows:
            row.pop("relevance_score", None)
        return [PolicyReference(**row) for row in rows]

    def _keywords(self, question: str) -> list[str]:
        tokens = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", question)
        important = []
        for token in tokens:
            if len(token) <= 1:
                continue
            important.append(token)

        domain_keywords = [
            "高校毕业生",
            "毕业生",
            "创业",
            "就业",
            "补贴",
            "补助",
            "人才",
            "见习",
            "实习",
            "培训",
            "落户",
            "住房",
            "社保",
        ]
        for keyword in domain_keywords:
            if keyword in question:
                important.append(keyword)

        return list(dict.fromkeys(important))[:6]
