# 검증 범위

## v0.1.1 — Workbench 통합

검증일: 2026-10-24 (Asia/Seoul).

- Windows / Python 3.12: 기존 `unittest` 22개 통과.
- Codex CLI 0.153.4의 별도 `CODEX_HOME`에서 플러그인을 설치하고 `codex mcp list --json`으로 실제 설정 해석 확인. 플러그인 루트로 해석된 `cwd`와 `LAW_API_OC` 전달 목록 확인.
- Codex가 해석한 실행 설정 및 Claude용 실행 설정으로 각각 MCP 초기화, 도구 3개 목록, `korean_law_setup` 호출 통과. 실제 OC 대신 테스트 문자열을 사용했으며 법제처 API는 호출하지 않음.
- Claude 플러그인 및 Workbench 마켓플레이스 manifest 검증 통과.
- 공개 소스 저장소는 `yunhyok/korean-law`, 설치 마켓플레이스는 비공개 `yunhyok/workbench`로 구분. 두 클라이언트의 설치 ID는 `korean-law@workbench`.
- Codex 호환 manifest는 인수 안의 플러그인 경로 치환에 의존하지 않고 상대 `cwd: "."`를 사용한다. [해당 버전의 설정 파서](https://github.com/openai/codex/blob/rust-v0.153.4/codex-rs/codex-mcp/src/plugin_config.rs#L236-L292).

실제 법제처 API 인증·조회와 재시작한 데스크톱 앱의 대화 내 도구 사용은 별도 확인이 필요하다.

## v0.1.0

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
