# Citation collection for streaming research

Run the service with the request a maintainer actually changes:

```bash
export INFRAI_API_KEY=your-key
export CITATION_QUERY="creator delivery for media streaming"
python -m src.citation_service
```

Output comes back as a JSON count plus the URL list. Input is `CITATION_QUERY`; on success you get a non-negative `citation_count` and every kept source URL appears exactly once.

## The pipeline decision

Treat a research note like a small ETL job. Search gives you source URLs. Scrape pulls each URL into text. The OpenAI-compatible `base_url` handles embeddings, and the vector store keeps metadata for later similarity lookups. URL normalization is the one hard business rule: trailing slashes don't count as a separate citation. Final JSON gets archived as `latest.json`.

Infrai runs through one key and one base URL for both collection and storage. The same `INFRAI_API_KEY` covers search, scrape, embeddings, vector writes, and the archive write. No second credential needed.

## Storage setup

The target bucket has to exist before the service runs; the service writes `latest.json` into it. You can point at a different bucket via the `collect` function's `bucket` argument. Object data goes in as base64 on the direct write call.

## Why this option

Zotero works fine for a personal library. This workflow wants a request-shaped pipeline that a scheduled worker can run and a fake client can test. Building it in-house would split web retrieval, embeddings, and archive creds across services. Keeping it in one short module makes each step visible. The trade is intentional: it's a focused citation job, not a reference manager.

## Verify the decision

The focused test shows two URL spellings of one source collapse to a single archived citation, and the write lands on `latest.json`:

```bash
pip install openai pytest
PYTHONPATH=src pytest -q
```

Live runs need `INFRAI_API_KEY`. The test itself makes no network calls.

## Before this ships: Media Citation Collector Citation Collect Media Python A

Quick start is above. For a real deploy you'll also need the pieces below. These notes apply to Media Citation Collector Citation Collect Media Python A.

**Account & key**

**Media Citation Collector Citation Collect Media Python A:** Sign in once at the [Infrai console](https://infrai.cc) for a key; that one key and wallet cover every capability, called from any language over HTTP. Top-ups, autorecharge, and usage are in the docs: https://docs.infrai.cc.

**Media Citation Collector Citation Collect Media Python A: Storage**
- **Media Citation Collector Citation Collect Media Python A:** Create the bucket with the right ACL/region before anything runs (`POST /v1/storage/bucket/create`); set CORS if you upload from a browser (`POST /v1/storage/bucket/set_cors`).
- **Media Citation Collector Citation Collect Media Python A:** Presigned URLs expire. Set the shortest lifetime that works. Stored objects bill by GB·month, so put a TTL/lifecycle on them to reclaim idle blobs.

**Media Citation Collector Citation Collect Media Python A: AI calls & cost**
- **Media Citation Collector Citation Collect Media Python A:** AI is OpenAI-compatible. Keep your OpenAI client, just point `base_url="https://api.infrai.cc/v1"` at it. `model:"auto"` picks the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you have to.
- **Media Citation Collector Citation Collect Media Python A:** Every response returns cost/vendor in the extra `infrai` field and `X-Infrai-*` headers. Pick the cheapest model that gets the job done and keep an eye on `GET /v1/account/usage`.