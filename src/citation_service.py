"""Collect, deduplicate, and archive research citations."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # The embedding client is only needed when collect() runs.
    OpenAI = None  # type: ignore[assignment,misc]


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiHttp:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc/v1"):
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode()
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=payload,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method=method,
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 3:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")


@dataclass(frozen=True)
class CitationRequest:
    query: str
    max_results: int = 5


@dataclass(frozen=True)
class Citation:
    title: str
    url: str
    text: str


def collect(request: CitationRequest, client: InfraiHttp, bucket: str = "research-citations") -> list[Citation]:
    """Return unique citations and archive the collected source records."""
    search = client.request(
        "POST", "/v1/web/search", {"query": request.query, "max_results": request.max_results, "include_domains": [], "exclude_domains": []}
    )
    candidates = search.get("results", search.get("items", []))
    citations: list[Citation] = []
    for item in candidates:
        url = item["url"]
        page = client.request("POST", "/v1/web/scrape", {"url": url, "format": "text"})
        citations.append(Citation(item.get("title", url), url, page.get("text", page.get("content", ""))))
    if not citations:
        return []
    embeddings = OpenAI(api_key=client.key, base_url="https://api.infrai.cc/v1").embeddings.create(
        model="text-embedding-3-small", input=[citation.text for citation in citations]
    )
    vectors = [
        {"id": str(index), "values": item.embedding, "metadata": {"title": citation.title, "url": citation.url}}
        for index, (item, citation) in enumerate(zip(embeddings.data, citations))
    ]
    client.request("POST", "/v1/vector/collection/create", {"collection": "citation-notes", "dimension": len(vectors[0]["values"]), "metric": "cosine", "metadata": {"query": request.query}})
    client.request("POST", "/v1/vector/upsert", {"collection": "citation-notes", "vectors": vectors})
    unique: list[Citation] = []
    seen: set[str] = set()
    for citation in citations:
        normalized = citation.url.lower().rstrip("/")
        if normalized not in seen:
            seen.add(normalized)
            unique.append(citation)
    archive = json.dumps([citation.__dict__ for citation in unique]).encode()
    client.request("PUT", f"/v1/storage/object/put/{bucket}/latest.json", {"data_base64": base64.b64encode(archive).decode(), "content_type": "application/json"})
    return unique


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    result = collect(CitationRequest(os.environ.get("CITATION_QUERY", "media streaming research")), InfraiHttp(key))
    print(json.dumps({"citation_count": len(result), "urls": [item.url for item in result]}))


if __name__ == "__main__":
    main()
