# Korean Law

법제처 **국가법령정보 공동활용 Open API**를 Codex, Claude Code, Claude Desktop 등에서 사용하는 로컬 MCP 서버와 공용 스킬입니다. 법제처의 공식 제품이 아닌 독립 오픈소스 프로젝트입니다.

**현재 상태: v0.1.1. 실제 API 성공 응답은 아직 검증하지 않았습니다.** 테스트의 법령 데이터는 합성 데이터입니다. 설치·MCP 통신·오류 처리 테스트와 실제 법제처 접속 검증은 구분합니다.

## 구성과 선택 이유

| 구성 | 역할 |
| --- | --- |
| MCP 서버 | 여러 AI 클라이언트에서 같은 검색·본문 조회 함수를 호출 |
| `korean-law` 스킬 | 현행/연혁·시행일 확인, 본문 조회, 정확한 근거 인용 절차 |
| Python CLI | MCP 없이도 조회 가능. Python 표준 라이브러리만 사용 |
| Codex / Claude Code 플러그인 | MCP와 스킬을 묶어서 Workbench 마켓플레이스에서 설치 |

설명만 있는 스킬보다 호출·오류 처리를 코드로 고정하는 편이 안정적이고, MCP만 제공하는 것보다 법령의 적용 시점과 인용 절차를 스킬로 안내하는 편이 적합합니다. 외부 서버, 데이터베이스, 웹 UI는 필요하지 않습니다. 공용 코드의 한 사본을 스킬 안에 두어 스킬만 복사해도 CLI가 동작합니다.

## 지원 범위

검색과 본문 조회: 시행일 기준 법령(`eflaw`), 공포일 기준 법령(`law`), 행정규칙(`admrul`), 자치법규(`ordin`), 판례(`prec`), 헌재결정례(`detc`), 법령해석례(`expc`), 행정심판례(`decc`). 법령의 특정 조문은 6자리 `JO`로 조회합니다.

현행 검색은 기본 `eflaw`, `nw=3`입니다. 연혁은 `nw=1`, 시행예정은 `nw=2`입니다. `MST`와 `efYd`는 판본을 고르는 한 쌍이며, `ID`는 현행을 선택합니다. [공식 목록 가이드](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsEfYdListGuide), [본문 가이드](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsEfYdInfoGuide).

전체 191개 API를 구현하지는 않습니다. HTML 전용 `lsHistory`, 국세청 제공 판례 본문, 세부 항·호·목 전용 API, 별표 파일 다운로드는 이 버전의 범위 밖입니다. 자세한 매개변수는 [API 참고](skills/korean-law/references/api.md)에 있습니다.

## 먼저: API 신청

회원가입 외에 **사용할 데이터별 공동활용 신청과 승인**이 필요합니다. 승인받은 API 인증값을 `LAW_API_OC`에 설정합니다. 예제의 `test`나 다른 사람의 OC를 사용하지 않습니다. [신청·환경변수 설정 안내](skills/korean-law/references/setup.md), [법제처 이용안내](https://open.law.go.kr/LSO/information/guide.do).

OC가 없어도 설치와 로컬 점검은 가능합니다. `doctor` / `korean_law_setup`은 값의 존재만 검사하며 승인 여부를 확인하지 않습니다. `.env`는 자동으로 읽지 않습니다.

## 설치

필수: Python 3.11 이상. MCP 설치는 [uv](https://docs.astral.sh/uv/getting-started/installation/)를 사용합니다. MCP SDK는 검증한 `2.3.0`으로 고정하고 의존성은 `uv.lock`으로 재현합니다.

```sh
git clone https://github.com/yunhyok/korean-law.git
cd korean-law
uv sync --frozen --extra mcp
uv run --frozen --extra mcp korean-law doctor
```

### Codex

마켓플레이스 주소는 [yunhyok/workbench](https://github.com/yunhyok/workbench)로 통일합니다. Workbench는 비공개 개인 마켓플레이스이므로 해당 저장소에 대한 GitHub 접근 권한이 필요합니다. 공개 소스와 릴리스는 이 `korean-law` 저장소에서 계속 관리합니다. Workbench 접근 권한이 없는 사용자는 아래 수동 설치를 사용할 수 있습니다.

```sh
codex plugin marketplace add https://github.com/yunhyok/workbench.git
codex plugin add korean-law@workbench
```

이미 Workbench가 등록되어 있다면 첫 명령 대신 `codex plugin marketplace upgrade workbench`로 목록을 갱신합니다. 플러그인은 스킬과 MCP 서버를 함께 설치하고 `LAW_API_OC`를 전달합니다. 환경변수 설정 후 Codex를 완전히 종료했다가 다시 실행합니다.

기존 수동 설치를 사용 중이라면 플러그인 설치와 MCP 동작을 확인한 다음 `codex mcp remove korean-law`로 기존 서버 등록을 제거하고, `~/.codex/skills/korean-law`를 스킬 검색 경로 밖에 백업해 중복 로드를 피합니다. OC 환경변수는 그대로 사용합니다.

#### 수동 설치

Workbench 플러그인과 수동 설치 중 하나만 사용합니다.

공용 스킬 설치(기존 다른 스킬을 수정하지 않음):

```sh
python scripts/install_skill.py --client codex
```

MCP 등록은 체크아웃의 **절대 경로**를 사용합니다. 아래 `/absolute/path/korean-law`를 실제 경로로 바꾸십시오. Windows도 `C:/.../korean-law` 형식을 쓸 수 있습니다.

```sh
codex mcp add korean-law -- uv run --frozen --directory "/absolute/path/korean-law" --extra mcp korean-law-mcp
```

`LAW_API_OC`를 MCP 프로세스에 전달하려면 Codex 설정의 해당 서버 블록에 다음 한 줄을 추가합니다. 다른 설정은 유지합니다.

```toml
[mcp_servers.korean-law]
# command, args는 위 등록 명령이 작성한 값을 유지
env_vars = ["LAW_API_OC"]
```

환경변수를 설정한 뒤 Codex를 다시 시작하고 새 채팅에서 `$korean-law 개인정보 보호법의 현행 제15조를 확인해 줘`처럼 요청합니다. [Codex MCP 공식 문서](https://developers.openai.com/codex/mcp).

### Claude Code 플러그인

```sh
claude plugin marketplace add yunhyok/workbench
claude plugin install korean-law@workbench
```

이미 Workbench가 등록되어 있다면 `claude plugin marketplace update workbench`로 목록을 갱신합니다. 기존 `yunhyok-law`에서 이전하는 경우 위 설치가 성공한 뒤 `claude plugin marketplace remove yunhyok-law`를 실행하면 이전 마켓플레이스와 그 플러그인이 제거됩니다. 새 설치 ID는 `korean-law@workbench`입니다.

`uv`가 PATH에 있고, Claude Code를 시작하는 환경에 `LAW_API_OC`가 있어야 합니다. 새 세션에서 `/korean-law:korean-law` 또는 자연어로 법령 조회를 요청합니다. 개발 중에는 `claude --plugin-dir "/absolute/path/korean-law"`로 로컬 플러그인을 읽을 수 있습니다. [Claude 플러그인 공식 문서](https://code.claude.com/docs/en/plugins-reference).

스킬만 쓰려면 플러그인 대신 `python scripts/install_skill.py --client claude`를 실행합니다. 두 방식을 동시에 설치할 필요는 없습니다.

### Claude Desktop / 다른 로컬 MCP 클라이언트

클라이언트의 MCP 설정에 아래 서버를 추가합니다. 실제 절대 경로와 승인 OC를 로컬 설정에서만 입력하십시오. `uv`를 찾지 못하면 실행파일의 절대 경로를 지정합니다. 기존 `mcpServers` 항목은 보존합니다.

```json
{
  "mcpServers": {
    "korean-law": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/absolute/path/korean-law", "--extra", "mcp", "korean-law-mcp"],
      "env": {"LAW_API_OC": "YOUR_APPROVED_OC"}
    }
  }
}
```

이것은 로컬 stdio 서버입니다. Claude 웹·ChatGPT 웹용 원격 커넥터나 공식 플러그인 디렉터리 등록을 제공하지 않습니다.

## 명령줄 예시

MCP 의존성 없이 실행할 수 있습니다. 아래 명령은 승인 OC를 설정한 뒤 실행합니다.

```sh
python skills/korean-law/scripts/law_api.py search "개인정보 보호법"
python skills/korean-law/scripts/law_api.py search "개인정보 보호법" --param nw=1
python skills/korean-law/scripts/law_api.py search "손해배상" --target prec --display 10
python skills/korean-law/scripts/law_api.py detail --target eflaw --id LAW_ID
# 검색 결과의 실제 법령일련번호/시행일자로 바꾸기:
python skills/korean-law/scripts/law_api.py detail --target eflaw --mst MASTER_NUMBER --effective-date YYYYMMDD --article 001500
```

`LAW_ID`, `MASTER_NUMBER`, `YYYYMMDD`는 자리 표시자입니다. CLI 출력은 JSON이며 실패 시 종료코드는 0이 아닙니다. `--param`으로 target별 공식 검색 매개변수를 전달할 수 있습니다.

## MCP 도구

| 도구 | 용도 |
| --- | --- |
| `korean_law_setup` | 네트워크 호출 없는 설정 점검과 신청 링크 |
| `search_legal_documents` | 데이터 종류·검색어·필터·페이지별 검색 |
| `get_legal_document` | 식별자로 본문 조회, 조문 선택, 긴 응답 분할 |

검색은 원래 응답 필드를 보존합니다. 본문은 JSON을 텍스트로 직렬화해 `content`에 반환합니다. `truncated=true`이면 `next_offset`부터 이어 읽고 `content_sha256`이 같은지 확인해야 합니다. 호출마다 다시 조회하므로 해시가 달라지면 처음부터 확인합니다. 가능하면 조문으로 범위를 줄이십시오. 조회시각은 UTC이며 법령 시행일과 다릅니다.

`request_url`은 OC를 뺀 진단 정보이므로 공개 원문 링크가 아닙니다. `guide_url`은 API 사용법의 출처입니다. 법적 결론은 본문·부칙·적용시점을 확인하고 별도로 확인한 국가법령정보센터 원문 링크와 법령명·조문·시행일 또는 사건번호를 인용합니다.

## 개발과 검증

```sh
uv sync --frozen --extra mcp
uv run --frozen --extra mcp python -m unittest discover -s tests -v
uv build
claude plugin validate .
```

테스트는 합성 응답과 로컬 MCP subprocess를 사용합니다. 승인 없는 실 API 호출을 하지 않으며 GitHub CI에도 OC가 필요하지 않습니다. 승인 후 현행법 검색→검색 결과의 MST/시행일로 조문 조회→공식 웹 원문 대조를 수행해야 실서비스 검증이 완료됩니다.

## 데이터와 보안

네트워크 요청은 고정된 `https://www.law.go.kr/DRF/` API에만 보냅니다. 리디렉션을 거부하고 시간·응답 크기를 제한합니다. OC는 환경변수에서 읽고 반환 URL과 오류에서 숨깁니다. 검색어는 법제처에 전송됩니다. 텔레메트리, 자동 수집, 영구 응답 캐시는 없습니다.

코드의 MIT 라이선스는 법령 데이터의 이용조건을 대체하지 않습니다. 데이터의 출처는 **법제처 국가법령정보센터**로 표시하고 [공식 이용조건](https://open.law.go.kr/LSO/information/guide.do)을 확인하십시오.
