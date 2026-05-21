"""LLM API client.

The client uses OpenAI-compatible Chat Completions API:
POST {LLM_BASE_URL}/chat/completions
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ai.config import LLMConfig


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.session = requests.Session()
        self.session.trust_env = not config.ignore_proxy

        retry = Retry(
            total=config.max_retries,
            connect=config.max_retries,
            read=config.max_retries,
            status=config.max_retries,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("POST",),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def chat(self, messages: list[dict[str, str]]) -> str:
        if not self.config.api_key:
            raise RuntimeError("LLM_API_KEY is not configured in .env")

        url = self.config.base_url.rstrip("/") + "/chat/completions"
        try:
            response = self.session.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": 0.2,
                },
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            response_text = exc.response.text[:1000] if exc.response is not None else ""
            raise RuntimeError(
                f"LLM API returned HTTP {exc.response.status_code}: {response_text}"
            ) from exc
        except requests.exceptions.SSLError as exc:
            proxy_hint = (
                "当前请求会读取系统代理环境变量；如果你的代理对 dashscope.aliyuncs.com "
                "握手失败，可以在 .env 中临时设置 LLM_IGNORE_PROXY=true 后再试。"
                if not self.config.ignore_proxy
                else "当前已设置 LLM_IGNORE_PROXY=true，说明这次请求没有使用系统代理。"
            )
            raise RuntimeError(f"LLM API SSL handshake failed. {proxy_hint}") from exc
        except requests.exceptions.ProxyError as exc:
            raise RuntimeError(
                "LLM API proxy connection failed. 请检查 HTTP_PROXY/HTTPS_PROXY "
                "或在 .env 中设置 LLM_IGNORE_PROXY=true 临时绕过代理。"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                "LLM API request timed out. 请检查网络/代理，或适当调大 LLM_TIMEOUT。"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "LLM API connection failed. 请先确认 dashscope.aliyuncs.com 可以访问。"
            ) from exc
        data = response.json()
        return data["choices"][0]["message"]["content"]
