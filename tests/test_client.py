"""Synthetic transport fixtures for the public client; no live API calls."""

from __future__ import annotations

import io
import json
import os
import urllib.error
import urllib.parse
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from korean_law import LawAPIError, LawClient
from korean_law.cli import main


class Response:
    def __init__(
        self,
        body=(
            b'{"LawSearch":{"totalCnt":"1"},"\\ubc95\\ub839ID":"1",'
            b'"\\ud589\\uc815\\uaddc\\uce59ID":"1","\\uc790\\uce58\\ubc95\\uaddcID":"1",'
            b'"\\ud310\\ub840\\uc815\\ubcf4\\uc77c\\ub828\\ubc88\\ud638":"1",'
            b'"\\ud5cc\\uc7ac\\uacb0\\uc815\\ub840\\uc77c\\ub828\\ubc88\\ud638":"1",'
            b'"\\ubc95\\ub839\\ud574\\uc11d\\ub840\\uc77c\\ub828\\ubc88\\ud638":"1",'
            b'"\\ud589\\uc815\\uc2ec\\ud310\\ub840\\uc77c\\ub828\\ubc88\\ud638":"1",'
            b'"\\uc870\\ubb38\\ub0b4\\uc6a9":"body","\\uc870\\ub0b4\\uc6a9":"body",'
            b'"\\ud310\\ub840\\ub0b4\\uc6a9":"body",'
            b'"\\uc804\\ubb38":"body","\\ud68c\\ub2f5":"body","\\uc8fc\\ubb38":"body"}'
        ),
        *,
        url=None,
        status=200,
        content_type="application/json",
    ):
        self.body = body
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.status

    def geturl(self):
        return self.url

    def read(self, amount):
        return self.body[:amount]


class Opener:
    def __init__(self, response=None, error=None):
        self.response = response or Response()
        self.error = error
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        if self.error:
            raise self.error
        self.response.url = self.response.url or request.full_url
        return self.response


class ClientTests(unittest.TestCase):
    def test_html_escaped_and_embedded_links_do_not_expose_oc(self):
        client = LawClient(oc="synthetic-only")
        for boundary in ("&amp;", "&#38;", "&#x26;", "&"):
            for key in ("OC", "oc", "%4f%43"):
                link = f'https://www.law.go.kr/DRF/lawService.do?ID=1{boundary}{key}=synthetic-only'
                for value in (link, f'<a href="{link}">본문</a>'):
                    self.assertNotIn("synthetic-only", client._sanitize_data(value))

    def test_missing_auth_fails_before_network(self):
        opener = Opener()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(LawAPIError, "LAW_API_OC"):
                LawClient(_opener=opener).search(query="자동차")
        self.assertEqual(opener.calls, [])

    def test_search_builds_encoded_url_and_redacts_oc(self):
        opener = Opener()
        result = LawClient("top-secret", _opener=opener).search(query="자동차 관리법", parameters={"sort": "ddes"})
        actual = urllib.parse.urlparse(opener.calls[0][0])
        query = urllib.parse.parse_qs(actual.query)
        self.assertEqual(actual.scheme, "https")
        self.assertEqual(query["OC"], ["top-secret"])
        self.assertEqual(query["nw"], ["3"])
        self.assertEqual(query["query"], ["자동차 관리법"])
        self.assertNotIn("top-secret", json.dumps(result, ensure_ascii=False))
        self.assertNotIn("OC=", result["request_url"])

    def test_nested_upstream_credentials_and_authenticated_links_are_redacted(self):
        secret = "name@example.com"
        upstream = {
            "LawSearch": {
                "totalCnt": "1",
                "law": [
                    {
                        "법령상세링크": "/DRF/lawService.do?target=law&%4F%43=name%40example.com&ID=1",
                        "nested": {"OC": secret, "echo": secret, "encoded_echo": "name%40example.com"},
                    }
                ],
            }
        }
        result = LawClient(secret, _opener=Opener(Response(json.dumps(upstream).encode()))).search()
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(secret, serialized)
        self.assertNotIn("name%40example.com", serialized)
        self.assertNotRegex(serialized, r"(?i)(?:%4f%43|OC)=")
        self.assertEqual(result["data"]["LawSearch"]["law"][0]["nested"]["echo"], "[REDACTED]")

    def test_search_history_uses_eflaw_nw_one_without_fallback(self):
        opener = Opener()
        LawClient("secret", _opener=opener).search(target="eflaw", parameters={"nw": "1"})
        query = urllib.parse.parse_qs(urllib.parse.urlparse(opener.calls[0][0]).query)
        self.assertEqual(query["target"], ["eflaw"])
        self.assertEqual(query["nw"], ["1"])

    def test_parameters_are_allowlisted_and_protected(self):
        client = LawClient("secret", _opener=Opener())
        with self.assertRaises(LawAPIError):
            client.search(target="law", parameters={"nw": 1})
        with self.assertRaises(LawAPIError):
            client.search(parameters={"OC": "replacement"})

    def test_eflaw_mst_requires_date_and_id_rejects_date(self):
        client = LawClient("secret", _opener=Opener())
        with self.assertRaisesRegex(LawAPIError, "requires effective_date"):
            client.detail("eflaw", mst="166520")
        with self.assertRaisesRegex(LawAPIError, "cannot be combined"):
            client.detail("eflaw", document_id="1747", effective_date="20151007")

    def test_eflaw_detail_builds_mst_date_and_validates_jo(self):
        opener = Opener()
        result = LawClient("secret", _opener=opener).detail(
            "eflaw", mst="166520", effective_date="20151007", article="001002"
        )
        query = urllib.parse.parse_qs(urllib.parse.urlparse(opener.calls[0][0]).query)
        self.assertEqual(query["MST"], ["166520"])
        self.assertEqual(query["efYd"], ["20151007"])
        self.assertEqual(query["JO"], ["001002"])
        self.assertIn("lsEfYdInfoGuide", result["guide_url"])
        with self.assertRaisesRegex(LawAPIError, "six-digit"):
            LawClient("secret", _opener=Opener()).detail("law", document_id="1747", article="10")
        with self.assertRaisesRegex(LawAPIError, "six-digit"):
            LawClient("secret", _opener=Opener()).detail("law", document_id="1747", article="１２３４５６")

    def test_dates_identifiers_and_paging_require_ascii_integers(self):
        client = LawClient("secret", _opener=Opener())
        for page in (1.5, True, "１２"):
            with self.subTest(page=page), self.assertRaises(LawAPIError):
                client.search(page=page)
        with self.assertRaises(LawAPIError):
            client.detail("law", document_id="１２３")
        for date in ("2026102", "２０２６１０２４", "20260230"):
            with self.subTest(date=date), self.assertRaises(LawAPIError):
                client.detail("eflaw", mst="1", effective_date=date)

    def test_redirect_and_http_errors_are_sanitized(self):
        redirected = Opener(Response(url="https://example.invalid/leak?OC=secret"))
        with self.assertRaisesRegex(LawAPIError, "redirect") as redirect_error:
            LawClient("secret", _opener=redirected).search()
        self.assertNotIn("secret", str(redirect_error.exception))

        http_error = urllib.error.HTTPError("https://host/?OC=secret", 503, "secret-body", {}, None)
        with self.assertRaisesRegex(LawAPIError, "HTTP 503") as error:
            LawClient("secret", _opener=Opener(error=http_error)).search()
        self.assertNotIn("secret", str(error.exception))

    def test_html_empty_and_malformed_json_are_distinct_failures(self):
        cases = [
            (Response(b"<html>error</html>", content_type="text/html"), "HTML"),
            (Response(b""), "empty"),
            (Response(b"not json"), "malformed JSON"),
            (Response(b"{}"), "malformed JSON envelope"),
        ]
        for response, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(LawAPIError, message):
                LawClient("secret", _opener=Opener(response)).search()

    def test_html_only_precedent_detail_is_explicitly_unsupported(self):
        response = Response(b"<html>precedent</html>", content_type="text/html")
        with self.assertRaisesRegex(LawAPIError, "HTML-only.*unsupported"):
            LawClient("secret", _opener=Opener(response)).detail("prec", document_id="228541")

    def test_oversized_response_is_rejected_without_parsing_a_prefix(self):
        body = b"{" + b" " * (8 * 1024 * 1024)
        with self.assertRaisesRegex(LawAPIError, "8 MiB"):
            LawClient("secret", _opener=Opener(Response(body))).search()

    def test_zero_results_and_success_preserve_upstream_data(self):
        upstream = {"LawSearch": {"totalCnt": "0", "law": []}}
        result = LawClient("secret", _opener=Opener(Response(json.dumps(upstream).encode()))).search()
        self.assertEqual(result["data"], upstream)
        self.assertEqual(result["target"], "eflaw")
        self.assertTrue(result["retrieved_at"].endswith("Z"))

    def test_error_and_unrecognized_envelopes_are_not_reported_as_results(self):
        failures = [
            ({"wrapper": {"errorCode": "AUTH", "message": "bad"}}, "error response"),
            ({"wrapper": {"resultCode": "500"}}, "error response"),
            ({"unexpected": "value"}, "unrecognized search"),
        ]
        for payload, message in failures:
            with self.subTest(payload=payload), self.assertRaisesRegex(LawAPIError, message):
                body = json.dumps(payload).encode()
                LawClient("secret", _opener=Opener(Response(body))).search()

        with self.assertRaisesRegex(LawAPIError, "unrecognized detail"):
            LawClient("secret", _opener=Opener(Response(b'{"something":"else"}'))).detail(
                "law", document_id="1"
            )

    def test_ordin_accepts_id_or_mst_but_other_nonlaw_targets_do_not(self):
        LawClient("secret", _opener=Opener()).detail("ordin", mst="1316146")
        with self.assertRaisesRegex(LawAPIError, "does not support mst"):
            LawClient("secret", _opener=Opener()).detail("prec", mst="228541")

    def test_doctor_is_offline_and_does_not_print_credential(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {"LAW_API_OC": "never-print-me"}, clear=True):
            with patch("korean_law.cli.LawClient") as client, redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(["doctor"])
        self.assertEqual(code, 0)
        self.assertFalse(client.called)
        self.assertNotIn("never-print-me", stdout.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["configured"], True)
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
