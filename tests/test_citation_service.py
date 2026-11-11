from citation_service import Citation, CitationRequest, collect


class FakeClient:
    key = "test-key"

    def __init__(self):
        self.calls = []

    def request(self, method, path, body):
        self.calls.append((method, path, body))
        if path.endswith("/search"):
            return {"results": [{"title": "A", "url": "https://example.test/a"}, {"title": "A copy", "url": "https://example.test/a/"}]}
        if path.endswith("/scrape"):
            return {"text": "streaming research notes"}
        return {}


def test_duplicate_urls_are_archived_once(monkeypatch):
    class Embedding:
        def __init__(self):
            self.data = [type("Item", (), {"embedding": [0.1, 0.2]})(), type("Item", (), {"embedding": [0.1, 0.2]})()]

    monkeypatch.setattr("citation_service.OpenAI", lambda **_: type("Client", (), {"embeddings": type("Embeddings", (), {"create": lambda *_args, **_kwargs: Embedding()})()})())
    client = FakeClient()
    result = collect(CitationRequest("media"), client)
    assert result == [Citation("A", "https://example.test/a", "streaming research notes")]
    assert client.calls[-1][1].endswith("/latest.json")
