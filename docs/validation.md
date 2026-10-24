# v0.1.0 검증 범위

검증일: 2026-10-24 (Asia/Seoul).

- Windows / Python 3.12: `unittest` **22개 통과**.
- 합성 응답으로 8개 target의 식별자·본문 필드 확인, 날짜/페이지/JO 검증, 인증값 제거, 오류/빈 응답/과대 응답 처리 확인.
- 실제 stdio subprocess로 MCP 초기화, 3개 도구 목록, 설정 점검, 인증값 미설정 오류, 합성 데이터 검색→본문 조회 통과.
- 긴 본문을 여러 조각으로 읽고 해시·복원 결과 확인.
- 스킬 `quick_validate.py`, Claude plugin/marketplace CLI 검증 통과.
- wheel/sdist 빌드, sdist 내 플러그인·스킬·테스트 파일 확인, 별도 환경에 의존성 없이 wheel 설치 후 CLI `doctor` 통과.
- 독립 검토의 HTML 이스케이프 링크 인증값 노출 지적을 수정하고 회귀 테스트 추가.
- GitHub Actions는 Linux/Windows × Python 3.11/3.13 조합을 검사한다. 실행 결과는 [Actions](https://github.com/yunhyok/korean-law/actions)에서 확인한다.

**실제 법제처 API 조회는 미검증**이다. 승인 OC가 없으므로 샘플·타인의 인증값으로 호출하지 않았다. 공식 문서와 합성 데이터 테스트는 운영 API 응답과의 호환성이나 사용승인을 입증하지 않는다. Claude Desktop GUI에서의 연결도 검증하지 않았다.

승인 후 [설정 안내](../skills/korean-law/references/setup.md)에 따라 OC를 설정하고, 현행법 검색 → 반환된 `(MST, 시행일자)`로 조문 조회 → 공식 웹 원문 대조를 수행한다. API 오류는 결과 0건으로 처리하지 않는다.
