"""Database access for policy documents."""

from typing import Optional

import pymysql

from crawler.config import DatabaseConfig
from crawler.models import PolicyDocument


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
            document.title,
            document.policy_number,
            document.issuing_department,
            document.publish_level,
            document.publish_date,
            document.status,
            document.source_url,
            document.full_text,
            document.summary,
        )
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                connection.commit()
                return cursor.lastrowid
