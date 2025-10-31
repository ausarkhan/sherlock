import json
import os

from sherlock_project.sherlock import sherlock, SherlockFuturesSession
from sherlock_project.notify import QueryNotify
from sherlock_project.result import QueryStatus


class DummyResponse:
    def __init__(self, status_code: int, text: str = "", encoding: str = "utf-8"):
        self.status_code = status_code
        self.text = text
        self.encoding = encoding
        self.elapsed = 0.0


class DummyFuture:
    def __init__(self, response):
        self._response = response

    def result(self):
        return self._response


def load_linkedin_manifest():
    base = os.path.dirname(os.path.dirname(__file__))
    data_file = os.path.join(base, "sherlock_project", "resources", "data.json")
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["LinkedIn"].copy()


def test_linkedin_999_marked_waf(monkeypatch):
    """
    If LinkedIn (or similar) responds with a non-standard code like 999,
    mark result as WAF (blocked), not AVAILABLE.
    """
    linkedin = load_linkedin_manifest()
    assert linkedin.get("errorType") == "status_code"

    site_data = {"LinkedIn": linkedin}

    # Patch SherlockFuturesSession.get to return a DummyFuture with status 999
    def fake_get(self, *args, **kwargs):
        resp = DummyResponse(status_code=999, text="")
        return DummyFuture(resp)

    monkeypatch.setattr(SherlockFuturesSession, "get", fake_get)

    qn = QueryNotify()
    results = sherlock(username="aryanj10", site_data=site_data, query_notify=qn)

    assert "LinkedIn" in results
    status = results["LinkedIn"]["status"].status
    assert status is QueryStatus.WAF, f"Expected LinkedIn to be marked WAF on 999, got {status}"
