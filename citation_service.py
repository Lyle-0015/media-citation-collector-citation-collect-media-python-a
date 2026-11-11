"""Compatibility imports for running the service from the repository root."""

from src import citation_service as _implementation

Citation = _implementation.Citation
CitationRequest = _implementation.CitationRequest
InfraiError = _implementation.InfraiError
InfraiHttp = _implementation.InfraiHttp
OpenAI = _implementation.OpenAI


def collect(request, client, bucket="research-citations"):
    # Keep monkeypatching the historical top-level import working in tests.
    _implementation.OpenAI = OpenAI
    return _implementation.collect(request, client, bucket)


__all__ = [
    "Citation",
    "CitationRequest",
    "InfraiError",
    "InfraiHttp",
    "OpenAI",
    "collect",
]
