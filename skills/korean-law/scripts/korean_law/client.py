"""Client for the official Korean Ministry of Government Legislation API."""

from __future__ import annotations

import json
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
DETAIL_URL = "https://www.law.go.kr/DRF/lawService.do"
GUIDE_URL = "https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName="
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
TARGETS = frozenset({"eflaw", "law", "admrul", "ordin", "prec", "detc", "expc", "decc"})

_GUIDES = {
    ("search", "eflaw"): "lsEfYdListGuide",
    ("detail", "eflaw"): "lsEfYdInfoGuide",
    ("search", "law"): "lsNwListGuide",
    ("detail", "law"): "lsNwInfoGuide",
    **{(kind, target): f"{target}{suffix}" for target in TARGETS - {"eflaw", "law"} for kind, suffix in (("search", "ListGuide"), ("detail", "InfoGuide"))},
}

_SEARCH_PARAMETERS = {
    "eflaw": {"search", "nw", "LID", "sort", "efYd", "date", "ancYd", "ancNo", "rrClsCd", "nb", "org", "knd", "gana", "popYn"},
    "law": {"search", "sort", "date", "efYd", "ancYd", "ancNo", "rrClsCd", "nb", "org", "knd", "lsChapNo", "gana", "popYn"},
    "admrul": {"nw", "search", "org", "knd", "gana", "sort", "date", "prmlYd", "modYd", "nb", "popYn"},
    "ordin": {"nw", "search", "sort", "date", "efYd", "ancYd", "ancNo", "nb", "org", "sborg", "knd", "rrClsCd", "ordinFd", "lsChapNo", "gana", "popYn"},
    "prec": {"search", "org", "curt", "JO", "gana", "sort", "date", "prncYd", "nb", "datSrcNm", "popYn"},
    "detc": {"search", "gana", "sort", "date", "edYd", "nb", "popYn"},
    "expc": {"search", "inq", "rpl", "gana", "itmno", "regYd", "explYd", "sort", "popYn"},
    "decc": {"search", "cls", "gana", "date", "dpaYd", "rslYd", "sort", "popYn"},
}

_DETAIL_FIELDS = {
    "eflaw": ({"법령ID", "법령일련번호"}, {"조문내용", "부칙내용", "별표내용", "개정문내용", "제개정이유내용"}),
    "law": ({"법령ID", "법령일련번호"}, {"조문내용", "부칙내용", "별표내용", "개정문내용", "제개정이유내용"}),
    "admrul": ({"행정규칙ID", "행정규칙일련번호", "행정규칙 일련번호"}, {"조문내용", "부칙내용", "별표내용"}),
    "ordin": ({"자치법규ID", "자치법규일련번호"}, {"조내용", "부칙내용", "별표내용", "개정문내용", "제개정이유내용"}),
    "prec": ({"판례정보일련번호", "판례일련번호"}, {"판례내용", "판시사항", "판결요지"}),
    "detc": ({"헌재결정례일련번호"}, {"판시사항", "결정요지", "전문"}),
    "expc": ({"법령해석례일련번호"}, {"질의요지", "회답", "이유"}),
    "decc": ({"행정심판례일련번호", "행정심판재결례일련번호"}, {"주문", "청구취지", "이유", "재결요지"}),
}


class LawAPIError(RuntimeError):
    """A safe, user-facing API or validation failure."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise urllib.error.HTTPError(req.full_url, code, "Redirect rejected", headers, fp)


class LawClient:
    """Access supported Korean law search and detail endpoints."""

    def __init__(self, oc: str | None = None, *, timeout: float = 30, _opener: Any = None):
        self.oc = oc if oc is not None else os.environ.get("LAW_API_OC")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.timeout = timeout
        self._opener = _opener or urllib.request.build_opener(_NoRedirect())

    def search(
        self,
        target: str = "eflaw",
        query: str = "",
        page: int = 1,
        display: int = 20,
        parameters: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search one supported official API target."""
        target = self._target(target)
        if not isinstance(query, str):
            raise LawAPIError("query must be a string")
        page = self._bounded_integer("page", page, 1, 2_147_483_647)
        display = self._bounded_integer("display", display, 1, 100)
        extras = self._search_parameters(target, parameters)
        if target == "eflaw" and "nw" not in extras:
            extras["nw"] = "3"
        params: dict[str, str] = {
            "OC": self._credential(),
            "target": target,
            "type": "JSON",
            "query": query,
            "page": str(page),
            "display": str(display),
            **extras,
        }
        return self._request("search", target, SEARCH_URL, params)

    def detail(
        self,
        target: str,
        document_id: str | int | None = None,
        mst: str | int | None = None,
        effective_date: str | int | None = None,
        article: str | int | None = None,
    ) -> dict[str, Any]:
        """Fetch one official document by the identifier supported by its guide."""
        target = self._target(target)
        document_id = self._identifier("document_id", document_id)
        mst = self._identifier("mst", mst)
        if (document_id is None) == (mst is None):
            raise LawAPIError("provide exactly one of document_id or mst")

        if mst is not None and target not in {"eflaw", "law", "ordin"}:
            raise LawAPIError(f"target {target!r} does not support mst detail lookup")
        if effective_date is not None and target != "eflaw":
            raise LawAPIError("effective_date is supported only for eflaw detail lookup")
        if target == "eflaw":
            if document_id is not None and effective_date is not None:
                raise LawAPIError("effective_date cannot be combined with document_id")
            if mst is not None and effective_date is None:
                raise LawAPIError("eflaw mst lookup requires effective_date")
        effective_date_value = self._date("effective_date", effective_date)

        if article is not None and target not in {"eflaw", "law"}:
            raise LawAPIError("article is supported only for eflaw and law detail lookup")
        article_value = None if article is None else str(article)
        if article_value is not None and not re.fullmatch(r"[0-9]{6}", article_value):
            raise LawAPIError("article must be the official six-digit JO value")

        params = {"OC": self._credential(), "target": target, "type": "JSON"}
        params["ID" if document_id is not None else "MST"] = document_id or mst  # type: ignore[assignment]
        if effective_date_value is not None:
            params["efYd"] = effective_date_value
        if article_value is not None:
            params["JO"] = article_value
        return self._request("detail", target, DETAIL_URL, params)

    def _request(self, kind: str, target: str, endpoint: str, params: Mapping[str, str]) -> dict[str, Any]:
        actual_url = endpoint + "?" + urllib.parse.urlencode(params)
        safe_params = {key: value for key, value in params.items() if key != "OC"}
        safe_url = endpoint + "?" + urllib.parse.urlencode(safe_params)
        request = urllib.request.Request(actual_url, headers={"Accept": "application/json", "User-Agent": "korean-law/0.1"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                status = getattr(response, "status", response.getcode())
                if status != 200:
                    raise LawAPIError(f"official API returned HTTP {status}")
                if response.geturl() != actual_url:
                    raise LawAPIError("official API redirect was rejected")
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                    raise LawAPIError("official API response exceeds the 8 MiB limit")
                body = response.read(MAX_RESPONSE_BYTES + 1)
                content_type = response.headers.get("Content-Type", "").lower()
        except LawAPIError:
            raise
        except urllib.error.HTTPError as exc:
            if 300 <= exc.code < 400:
                raise LawAPIError("official API redirect was rejected") from None
            raise LawAPIError(f"official API returned HTTP {exc.code}") from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError, ValueError):
            raise LawAPIError("official API request failed") from None

        if len(body) > MAX_RESPONSE_BYTES:
            raise LawAPIError("official API response exceeds the 8 MiB limit")
        if not body.strip():
            raise LawAPIError("official API returned an empty response")
        if "text/html" in content_type or body.lstrip().startswith((b"<", b"<!")):
            if kind == "detail" and target == "prec":
                raise LawAPIError("this prec detail is HTML-only and unsupported by this JSON client")
            raise LawAPIError("official API returned HTML instead of JSON")
        try:
            data = json.loads(body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise LawAPIError("official API returned malformed JSON") from None
        if not isinstance(data, dict) or not data:
            raise LawAPIError("official API returned a malformed JSON envelope")
        self._validate_payload(kind, target, data)

        return {
            "data": self._sanitize_data(data),
            "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "request_url": safe_url,
            "guide_url": GUIDE_URL + _GUIDES[(kind, target)],
            "target": target,
            "warnings": ["request_url omits OC and is not directly runnable without authentication."],
        }

    @staticmethod
    def _validate_payload(kind: str, target: str, data: dict[str, Any]) -> None:
        fields: list[tuple[str, Any]] = []

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    fields.append((str(key), item))
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(data)
        for key, value in fields:
            lowered = key.lower()
            if lowered in {"error", "errors", "errorcode", "error_code"}:
                raise LawAPIError("official API returned an error response")
            if lowered in {"resultcode", "result_code"} and str(value).strip().lower() not in {
                "0",
                "00",
                "0000",
                "success",
            }:
                raise LawAPIError("official API returned an error response")

        if kind == "search":
            totals = [value for key, value in fields if key == "totalCnt"]
            if not totals or any(not re.fullmatch(r"[0-9]+", str(value)) for value in totals):
                raise LawAPIError("official API returned an unrecognized search envelope")
            return

        identifiers, bodies = _DETAIL_FIELDS[target]
        has_identifier = any(key in identifiers and value not in (None, "") for key, value in fields)
        has_body = any(key in bodies and value not in (None, "", [], {}) for key, value in fields)
        if not has_identifier or not has_body:
            raise LawAPIError("official API returned an unrecognized detail envelope")

    def _credential(self) -> str:
        if not isinstance(self.oc, str) or not self.oc.strip():
            raise LawAPIError("LAW_API_OC is not configured")
        return self.oc.strip()

    @staticmethod
    def _target(target: str) -> str:
        if not isinstance(target, str) or target not in TARGETS:
            raise LawAPIError(f"target must be one of: {', '.join(sorted(TARGETS))}")
        return target

    @staticmethod
    def _bounded_integer(name: str, value: Any, minimum: int, maximum: int) -> int:
        if isinstance(value, bool) or not (
            isinstance(value, int) or isinstance(value, str) and re.fullmatch(r"[0-9]+", value)
        ):
            raise LawAPIError(f"{name} must be an integer from {minimum} to {maximum}")
        number = int(value)
        if not minimum <= number <= maximum:
            raise LawAPIError(f"{name} must be an integer from {minimum} to {maximum}")
        return number

    @staticmethod
    def _identifier(name: str, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
            raise LawAPIError(f"{name} must contain digits only")
        return str(value)

    @staticmethod
    def _date(name: str, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value)
        if not re.fullmatch(r"[0-9]{8}", text):
            raise LawAPIError(f"{name} must be a valid YYYYMMDD date")
        try:
            datetime.strptime(text, "%Y%m%d")
        except (TypeError, ValueError):
            raise LawAPIError(f"{name} must be a valid YYYYMMDD date") from None
        return text

    def _sanitize_data(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "[REDACTED]" if str(key).lower() == "oc" else self._sanitize_data(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._sanitize_data(item) for item in value]
        if not isinstance(value, str):
            return value
        credential = self._credential()
        if value == credential or urllib.parse.unquote(value) == credential:
            return "[REDACTED]"
        # Legal body fields can embed HTML-escaped links as well as plain URLs.
        value = re.sub(
            r"([?&](?:amp;|#0*38;|#x0*26;)?)([^=&\s\"'<>]+)=([^&\s\"'<>]*)",
            lambda match: match[1] + match[2] + "=[REDACTED]"
            if urllib.parse.unquote(match[2]).lower() == "oc" else match[0],
            value,
            flags=re.IGNORECASE,
        )
        if "?" not in value:
            return value
        if any(char in value for char in '<>"\'') or "&amp;" in value or "&#" in value:
            return value
        parts = urllib.parse.urlsplit(value)
        query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        if not any(key.lower() == "oc" for key, _ in query):
            return value
        return urllib.parse.urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode([(key, item) for key, item in query if key.lower() != "oc"]), parts.fragment)
        )

    @staticmethod
    def _search_parameters(target: str, parameters: Mapping[str, Any] | None) -> dict[str, str]:
        if parameters is None:
            return {}
        if not isinstance(parameters, Mapping):
            raise LawAPIError("parameters must be a mapping")
        extras: dict[str, str] = {}
        for key, value in parameters.items():
            if not isinstance(key, str):
                raise LawAPIError("parameter names must be strings")
            if key.lower() in {"oc", "target", "type"}:
                raise LawAPIError(f"parameter {key!r} cannot override a protected field")
            if key not in _SEARCH_PARAMETERS[target]:
                raise LawAPIError(f"parameter {key!r} is not supported for target {target!r}")
            if value is None or isinstance(value, (dict, list, tuple, set)):
                raise LawAPIError(f"parameter {key!r} must have one scalar value")
            extras[key] = str(value)
        return extras
