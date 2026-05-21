"""Configuration helpers for the crawler."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass(frozen=True)
class CrawlerConfig:
    request_timeout: int
    crawl_delay_seconds: float
    database: DatabaseConfig


def load_config() -> CrawlerConfig:
    return CrawlerConfig(
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "15")),
        crawl_delay_seconds=float(os.getenv("CRAWL_DELAY_SECONDS", "1")),
        database=DatabaseConfig(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "policy_user"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "xiamen_policy_ai"),
        ),
    )
