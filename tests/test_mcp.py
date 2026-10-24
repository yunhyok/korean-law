"""Wire-level tests with synthetic data; never contact the law API."""

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from korean_law import server


class ContentTests(unittest.TestCase):
    def test_chunks_reconstruct_document(self):
        data = {"법령": {"조문내용": "합성 테스트 조문" * 1500}}
        with patch.object(server.LawClient, "detail", side_effect=lambda *args: {"data": data, "target": "eflaw"}):
            parts, offset, digest = [], 0, None
            while True:
                result = server.get_legal_document("eflaw", document_id="1", offset=offset, max_chars=1000)
                parts.append(result["content"])
                if digest:
                    self.assertEqual(digest, result["content_sha256"])
                digest = result["content_sha256"]
                if not result["truncated"]:
                    self.assertIsNone(result["next_offset"])
                    break
                offset = result["next_offset"]
            self.assertEqual(json.loads("".join(parts)), data)

    def test_invalid_offsets_do_not_fetch(self):
        with patch.object(server.LawClient, "detail") as fetch:
            for args in ({"offset": -1}, {"max_chars": 100001}, {"offset": True}):
                with self.assertRaises(server.ToolError):
                    server.get_legal_document("eflaw", document_id="1", **args)
            fetch.assert_not_called()


class MCPWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_server_missing_credential_and_schemas(self):
        # An empty value overrides any developer machine credential; no network is possible.
        env = {**os.environ, "LAW_API_OC": "", "PYTHONIOENCODING": "utf-8"}
        parameters = StdioServerParameters(command=sys.executable, args=["-m", "korean_law.server"], env=env)
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=20) as session:
                initialized = await session.initialize()
                self.assertEqual(initialized.server_info.name, "korean-law")
                tools = (await session.list_tools()).tools
                self.assertEqual({tool.name for tool in tools}, {
                    "korean_law_setup", "search_legal_documents", "get_legal_document"
                })
                self.assertTrue(all(tool.annotations.read_only_hint for tool in tools))
                result = await session.call_tool("korean_law_setup", {})
                self.assertFalse(result.is_error)
                self.assertFalse(result.structured_content["configured"])
                failed = await session.call_tool("search_legal_documents", {"query": "합성 테스트"})
                self.assertTrue(failed.is_error)
                self.assertIn("LAW_API_OC", " ".join(item.text for item in failed.content))

    async def test_search_and_detail_over_stdio_with_synthetic_transport(self):
        fixture = Path(__file__).parent / "mcp_fixture_server.py"
        parameters = StdioServerParameters(command=sys.executable, args=[str(fixture)], env={**os.environ, "LAW_API_OC": ""})
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=20) as session:
                await session.initialize()
                found = await session.call_tool("search_legal_documents", {"query": "합성법"})
                self.assertFalse(found.is_error)
                self.assertEqual(found.structured_content["data"]["LawSearch"]["totalCnt"], "1")
                detail = await session.call_tool("get_legal_document", {
                    "target": "eflaw", "mst": "123456", "effective_date": "20260101", "article": "000100"
                })
                self.assertFalse(detail.is_error)
                self.assertIn("합성 조문", detail.structured_content["content"])
                self.assertFalse(detail.structured_content["truncated"])
