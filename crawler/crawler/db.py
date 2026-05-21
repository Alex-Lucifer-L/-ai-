"""Database access for policy documents."""

from typing import Optional

import pymysql

from crawler.config import DatabaseConfig
from crawler.extractors.region_matcher import RegionMatch
from crawler.models import PolicyDocument, PolicyItemCandidate, StoredPolicyItem


def _clip(value: Optional[str], max_length: int) -> Optional[str]:
    if value is None:
        return None
    return value[:max_length]


class PolicyDocumentRepository:
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

    def find_id_by_source_url(self, source_url: str) -> Optional[int]:
        sql = "SELECT document_id FROM policy_document WHERE source_url = %s LIMIT 1"
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (source_url,))
                row = cursor.fetchone()
        return row["document_id"] if row else None

    def insert_if_not_exists(self, document: PolicyDocument) -> int:
        existing_id = self.find_id_by_source_url(document.source_url)
        if existing_id is not None:
            return existing_id

        sql = """
            INSERT INTO policy_document (
                title,
                policy_number,
                issuing_department,
                publish_level,
                publish_date,
                status,
                source_url,
                full_text,
                summary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            _clip(document.title, 500),
            _clip(document.policy_number, 100),
            _clip(document.issuing_department, 255),
            _clip(document.publish_level, 30),
            document.publish_date,
            _clip(document.status, 30),
            _clip(document.source_url, 1000),
            document.full_text,
            document.summary,
        )
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                connection.commit()
                return cursor.lastrowid

    def list_documents(self, limit: int = 20, document_id: Optional[int] = None) -> list[PolicyDocument]:
        sql = """
            SELECT
                document_id,
                title,
                policy_number,
                issuing_department,
                publish_level,
                publish_date,
                status,
                source_url,
                full_text,
                summary
            FROM policy_document
            WHERE full_text IS NOT NULL
              AND full_text <> ''
        """
        params: list[object] = []
        if document_id is not None:
            sql += " AND document_id = %s"
            params.append(document_id)
        sql += " ORDER BY publish_date DESC, document_id DESC LIMIT %s"
        params.append(limit)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

        return [
            PolicyDocument(
                document_id=row["document_id"],
                title=row["title"],
                policy_number=row["policy_number"],
                issuing_department=row["issuing_department"],
                publish_level=row["publish_level"],
                publish_date=row["publish_date"],
                status=row["status"],
                source_url=row["source_url"],
                full_text=row["full_text"],
                summary=row["summary"],
            )
            for row in rows
        ]

    def category_id_by_name(self, category_name: str) -> int:
        sql = "SELECT category_id FROM category WHERE category_name = %s LIMIT 1"
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (category_name,))
                row = cursor.fetchone()
        if not row:
            raise ValueError(f"Category not found: {category_name}")
        return row["category_id"]

    def find_item_id_for_document(self, document_id: int, item_name: str) -> Optional[int]:
        sql = """
            SELECT pi.item_id
            FROM policy_item pi
            JOIN document_item di ON pi.item_id = di.item_id
            WHERE di.document_id = %s
              AND pi.item_name = %s
            LIMIT 1
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (document_id, item_name))
                row = cursor.fetchone()
        return row["item_id"] if row else None

    def insert_policy_item_for_document(
        self,
        document_id: int,
        item: PolicyItemCandidate,
    ) -> int:
        existing_id = self.find_item_id_for_document(document_id, item.item_name)
        if existing_id is not None:
            return existing_id

        category_id = self.category_id_by_name(item.category_name)
        insert_item_sql = """
            INSERT INTO policy_item (
                category_id,
                item_name,
                target_group_text,
                conditions_text,
                support_content,
                subsidy_standard,
                application_materials,
                application_process,
                application_channel,
                keywords,
                status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        insert_relation_sql = """
            INSERT INTO document_item (
                document_id,
                item_id,
                relation_type,
                original_excerpt,
                note
            ) VALUES (%s, %s, %s, %s, %s)
        """
        item_params = (
            category_id,
            _clip(item.item_name, 300),
            item.target_group_text,
            item.conditions_text,
            item.support_content,
            item.subsidy_standard,
            item.application_materials,
            item.application_process,
            _clip(item.application_channel, 500),
            item.keywords,
            _clip(item.status, 30),
        )

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(insert_item_sql, item_params)
                item_id = cursor.lastrowid
                cursor.execute(
                    insert_relation_sql,
                    (
                        document_id,
                        item_id,
                        "extracted",
                        item.original_excerpt,
                        "规则抽取生成，建议人工复核",
                    ),
                )
                connection.commit()
                return item_id

    def list_policy_items_for_region_backfill(
        self,
        limit: int = 100,
        item_id: Optional[int] = None,
        include_existing: bool = False,
    ) -> list[StoredPolicyItem]:
        sql = """
            SELECT
                pi.item_id,
                di.document_id,
                pi.item_name,
                c.category_name,
                pi.status,
                pd.publish_level,
                CONCAT_WS(
                    '\n',
                    pi.item_name,
                    c.category_name,
                    pi.target_group_text,
                    pi.conditions_text,
                    pi.support_content,
                    pi.subsidy_standard,
                    pi.application_materials,
                    pi.application_process,
                    pi.application_channel,
                    di.original_excerpt,
                    pd.title
                ) AS match_text
            FROM policy_item pi
            JOIN category c ON pi.category_id = c.category_id
            JOIN document_item di ON pi.item_id = di.item_id
            JOIN policy_document pd ON di.document_id = pd.document_id
            WHERE 1 = 1
              AND pi.status <> 'review_noise'
        """
        params: list[object] = []
        if item_id is not None:
            sql += " AND pi.item_id = %s"
            params.append(item_id)
        if not include_existing:
            sql += """
                AND NOT EXISTS (
                    SELECT 1
                    FROM item_region ir
                    WHERE ir.item_id = pi.item_id
                )
            """
        sql += " ORDER BY pi.item_id LIMIT %s"
        params.append(limit)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

        return [
            StoredPolicyItem(
                item_id=row["item_id"],
                document_id=row["document_id"],
                item_name=row["item_name"],
                category_name=row["category_name"],
                publish_level=row["publish_level"],
                text=row["match_text"] or "",
                status=row["status"],
            )
            for row in rows
        ]

    def list_policy_items_for_quality_review(
        self,
        limit: int = 200,
        item_id: Optional[int] = None,
        include_noise: bool = False,
    ) -> list[StoredPolicyItem]:
        sql = """
            SELECT
                pi.item_id,
                di.document_id,
                pi.item_name,
                c.category_name,
                pi.status,
                pd.publish_level,
                CONCAT_WS(
                    '\n',
                    pi.item_name,
                    c.category_name,
                    pi.target_group_text,
                    pi.conditions_text,
                    pi.support_content,
                    pi.subsidy_standard,
                    pi.application_materials,
                    pi.application_process,
                    pi.application_channel,
                    di.original_excerpt,
                    pd.title
                ) AS match_text
            FROM policy_item pi
            JOIN category c ON pi.category_id = c.category_id
            JOIN document_item di ON pi.item_id = di.item_id
            JOIN policy_document pd ON di.document_id = pd.document_id
            WHERE 1 = 1
        """
        params: list[object] = []
        if item_id is not None:
            sql += " AND pi.item_id = %s"
            params.append(item_id)
        if not include_noise:
            sql += " AND pi.status <> 'review_noise'"
        sql += " ORDER BY pi.item_id LIMIT %s"
        params.append(limit)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

        return [
            StoredPolicyItem(
                item_id=row["item_id"],
                document_id=row["document_id"],
                item_name=row["item_name"],
                category_name=row["category_name"],
                publish_level=row["publish_level"],
                text=row["match_text"] or "",
                status=row["status"],
            )
            for row in rows
        ]

    def region_id_by_name(self, region_name: str) -> int:
        sql = "SELECT region_id FROM region WHERE region_name = %s LIMIT 1"
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (region_name,))
                row = cursor.fetchone()
        if not row:
            raise ValueError(f"Region not found: {region_name}")
        return row["region_id"]

    def insert_item_region_if_not_exists(self, item_id: int, match: RegionMatch) -> bool:
        region_id = self.region_id_by_name(match.region_name)
        sql = """
            INSERT IGNORE INTO item_region (
                item_id,
                region_id,
                applicability_note,
                applicability_type
            ) VALUES (%s, %s, %s, %s)
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        item_id,
                        region_id,
                        _clip(match.applicability_note, 500),
                        _clip(match.applicability_type, 50),
                    ),
                )
                connection.commit()
                return cursor.rowcount > 0

    def mark_policy_items_review_noise(self, item_ids: list[int]) -> int:
        if not item_ids:
            return 0

        placeholders = ",".join(["%s"] * len(item_ids))
        sql = f"""
            UPDATE policy_item
            SET status = 'review_noise'
            WHERE item_id IN ({placeholders})
              AND status <> 'review_noise'
        """
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, item_ids)
                connection.commit()
                return cursor.rowcount

    def update_policy_item_category(self, item_id: int, category_name: str) -> bool:
        category_id = self.category_id_by_name(category_name)
        sql = "UPDATE policy_item SET category_id = %s WHERE item_id = %s AND category_id <> %s"
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (category_id, item_id, category_id))
                connection.commit()
                return cursor.rowcount > 0
