# 법제처 API 설정

이 프로젝트는 법제처 국가법령정보 공동활용 API를 사용한다. 승인된 `OC`가 없으면 API를 호출하지 않으며, 저장소에 인증값을 넣지 않는다.

## 1. 공식 신청

1. [국가법령정보 공동활용 회원가입](https://open.law.go.kr/LSO/main.do)을 완료한다.
2. 로그인 후 [OPEN API 신청](https://open.law.go.kr/LSO/openApi/cuAskList.do)에서 필요한 법령정보 서비스를 선택해 활용신청을 제출한다.
3. 담당자 승인 후 [API 인증키 관리](https://open.law.go.kr/LSO/usr/usrOcInfoMod.do)에서 발급된 `OC`를 확인한다.

공식 이용안내는 회원가입과 활용신청을 모두 요구하며, 모든 데이터 활용은 승인 이후 가능하다고 명시한다. 승인 처리는 신청 후 1–2일 이내로 안내되어 있다. 문서 예시의 `OC=test`는 샘플일 뿐 실제 인증값이 아니다.

## 2. 환경변수

환경변수 이름은 `LAW_API_OC` 하나만 사용한다. 이메일 주소의 일부, 임의 문자열, 문서 샘플값을 인증값으로 추측하지 않는다.

PowerShell:

```powershell
$env:LAW_API_OC = "발급받은_OC"
```

Bash:

```bash
export LAW_API_OC='발급받은_OC'
```

현재 셸에서만 적용되는 설정이다. 영구 사용자 환경변수나 비밀 저장소 설정은 각 호스트의 정책에 맞춰 별도로 관리하며, `.env`, 로그, 커밋, 이슈, 공개 프롬프트에 `OC`를 기록하지 않는다.

## 3. 호스트 재시작과 확인

환경변수를 설정한 뒤 Codex나 Claude 호스트를 재시작해 새 프로세스가 값을 읽게 한다. `doctor` 명령은 값의 존재 여부만 확인하고 인증값 자체를 출력하지 않아야 한다.

```text
python <skill-dir>/scripts/law_api.py doctor
```

승인 전에는 `search`나 `detail`을 실행하지 않는다. 승인 후에도 실제 API 조회가 성공했다고 보고하기 전에 HTTP 상태, 응답 형식, 목록→본문 식별자, 법령 기준일을 확인한다.

## 4. 현재 범위

v0.1은 `eflaw`, `law`, `admrul`, `ordin`, `prec`, `detc`, `expc`, `decc`의 JSON 검색·본문을 중심으로 한다. `eflaw` 검색 기본값은 현행(`nw=3`)이고 연혁은 `nw=1`이다. 별도 `lsHistory` API는 공식 가이드가 HTML만 문서화하므로 이 버전의 핵심 API에서 제외한다. 국세청 판례 본문도 공식 가이드상 HTML 전용이다.

API 오류 응답의 공통 JSON/XML 형식은 공식 가이드에 정의되어 있지 않다. 클라이언트는 상태 코드와 응답 형식을 확인하고, 인증값이 포함될 수 있는 오류 원문 대신 안전한 오류 메시지를 반환한다.

법령 답변을 만들 때는 제목 검색 결과만 인용하지 않는다. 검색→상세 본문 순서로 조회하고, 관련 법령의 시행일·판본·조문을 확인한 뒤 공개 `law.go.kr` 원문 링크를 제목, 조문 또는 사건 식별자, 기준일과 함께 제시한다. API가 실제로 호출되지 않은 경우 웹 원문 검증으로 구분해 표시하며 API 조회로 가장하지 않는다.

## 공식 참고

- [이용안내](https://open.law.go.kr/LSO/information/guide.do)
- [OPEN API 활용방법](https://open.law.go.kr/LSO/openApi/openApiManual.do)
- [OPEN API 활용가이드](https://open.law.go.kr/LSO/openApi/guideList.do)
