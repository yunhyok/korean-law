"""Synthetic transport only, launched by test_mcp. Not a live API fixture."""

import json

from korean_law import server
from korean_law.client import LawClient


class Response:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, url):
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def getcode(self):
        return 200

    def geturl(self):
        return self.url

    def read(self, size):
        if "lawSearch.do" in self.url:
            data = {"LawSearch": {"totalCnt": "1", "law": {"법령명한글": "합성법", "법령일련번호": "123456", "시행일자": "20260101"}}}
        else:
            data = {"법령": {"기본정보": {"법령ID": "123", "법령명_한글": "합성법"}, "조문": {"조문단위": {"조문번호": "1", "조문내용": "합성 조문"}}}}
        return json.dumps(data, ensure_ascii=False).encode("utf-8")[:size]


class Opener:
    def open(self, request, timeout):
        return Response(request.full_url)


server.LawClient = lambda: LawClient(oc="synthetic-only", _opener=Opener())
server.main()
