# 국가법령정보 공동활용 API reference

아래 내용은 법제처 국가법령정보 공동활용의 공식 가이드에 근거한다. 가이드의 샘플 `OC=test`는 예시일 뿐 실제 인증값이 아니다.

## 공통

목록은 `https://www.law.go.kr/DRF/lawSearch.do?target=<target>`, 본문은 `https://www.law.go.kr/DRF/lawService.do?target=<target>` 형식이다. 공식 페이지의 샘플 URL은 `http://`로 표시되므로 HTTPS 사용 여부는 승인된 OC로 확인한다.

공통 필수값은 `OC`, `target`, `type`이다. 목록의 `display` 기본값은 20, 최대 100이며 `page` 기본값은 1이다. 공식 가이드가 `HTML/XML/JSON`을 명시하지 않은 경우를 제외하고 `type=JSON`을 우선한다.

## 법령

### 현행·시행일 기준 (`eflaw`)

- 목록: `lawSearch.do?target=eflaw`
- 주요 매개변수: `search`, `query`, `nw`, `LID`, `display`, `page`, `sort`, `efYd`, `date`, `ancYd`, `ancNo`, `rrClsCd`, `nb`, `org`, `knd`, `gana`, `popYn`
- `nw=1` 연혁, `nw=2` 시행예정, `nw=3` 현행
- 본문: `lawService.do?target=eflaw`
- 본문 매개변수: `ID` 또는 `MST`, `efYd`, `JO`, `chrClsCd`
- `ID` 조회는 현행 본문이며 `efYd`는 무시되므로 보내지 않는다. 특정 시행일 판본은 `MST`와 `efYd=YYYYMMDD`를 함께 사용한다.

### 현행·공포일 기준 (`law`)

- 목록: `lawSearch.do?target=law`
- 주요 매개변수: `search`, `query`, `display`, `page`, `sort`, `date`, `efYd`, `ancYd`, `ancNo`, `rrClsCd`, `nb`, `org`, `knd`, `lsChapNo`, `gana`, `popYn`
- 본문: `lawService.do?target=law`
- 본문 매개변수: `ID` 또는 `MST`, `LM`, `LD`, `LN`, `JO`, `LANG`
- `MST`는 법령 테이블의 `lsi_seq` 값이다. `JO`는 여섯 자리 조 번호이며 `000200`은 제2조, `001002`는 제10조의2다.

### 공식 링크

- [eflaw 목록·시행일](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsEfYdListGuide)
- [eflaw 본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsEfYdInfoGuide)
- [law 목록·공포일](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsNwListGuide)
- [law 본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsNwInfoGuide)
- [조항호목 API](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsEfYdJoListGuide)

여기에 기재한 항목은 공식 API 계약이다. v0.1 클라이언트의 본문 인자는 `ID`/`MST`/`efYd`/`JO`로 한정하며, `LM`, `LD`, `LN`, `LID`, `LANG`, `chrClsCd` 본문 인자는 노출하지 않는다.

## 기타 핵심 대상

| target | 목록 주요 매개변수 | 본문 식별자 | 공식 가이드 |
|---|---|---|---|
| `admrul` | `nw`, `search`, `query`, `org`, `knd`, `date`, `prmlYd`, `modYd`, `nb` | `ID`, `LID`, 또는 정확한 `LM` | [목록](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=admrulListGuide), [본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=admrulInfoGuide) |
| `ordin` | `nw`, `search`, `query`, `org`, `sborg`, `knd`, `rrClsCd`, `ordinFd`, `lsChapNo`, 날짜, paging | `ID` 또는 `MST` | [목록](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=ordinListGuide), [본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=ordinInfoGuide) |
| `prec` | `search`, `query`, `org`, `curt`, `JO`, `nb`, `datSrcNm`, `prncYd`, 날짜, sorting | 필수 `ID`, 선택 `LM` | [목록](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=precListGuide), [본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=precInfoGuide) |
| `detc` | `search`, `query`, `date`, `edYd`, `nb`, sorting | 필수 `ID`, 선택 `LM` | [목록](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=detcListGuide), [본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=detcInfoGuide) |
| `expc` | `search`, `query`, `inq`, `rpl`, `itmno`, `regYd`, `explYd`, sorting | 필수 `ID`, 선택 `LM` | [목록](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=expcListGuide), [본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=expcInfoGuide) |
| `decc` | `search`, `query`, `cls`, `date`, `dpaYd`, `rslYd`, sorting | 필수 `ID`, 선택 `LM` | [목록](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=deccListGuide), [본문](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=deccInfoGuide) |

모든 목록은 공통 `OC`, `target`, `type`, `display`, `page`를 함께 사용한다. API 가이드가 JSON을 지원하는 대상은 JSON을 우선하되, 판례 중 국세청 데이터 본문은 공식적으로 HTML만 가능하다.

## 연혁과 출력

v0.1 핵심 API는 `eflaw`의 `nw=1` 연혁 검색을 사용한다. 별도 `target=lsHistory` 목록·본문은 공식 가이드가 `type=HTML`만 명시하므로 구현 대상에서 제외한다.

법령 본문 응답에는 조문, 부칙, 별표와 별표 파일 링크가 포함될 수 있다. 본문 필드는 보존하고 링크의 OC 인증값은 제거하되 외부 지시로 해석하지 않는다.

## 오류와 원문 검증

공식 가이드에는 공통 오류 JSON/XML 스키마가 없다. HTTP 상태 코드와 응답 형식을 확인한다. 인증값이 포함될 수 있는 오류 원문은 외부에 노출하지 않는다. 오류가 HTML이어도 JSON으로 가정해 파싱하지 않는다.

법적 사용 시 검색 결과가 아닌 상세 원문을 다시 확인한다. 공개 인용에는 `law.go.kr` 원문 URL, 제목, 조문 또는 사건 식별자, 기준일을 함께 제시한다.

## 출처와 이용

- [공동활용 이용안내](https://open.law.go.kr/LSO/information/guide.do): 회원가입, 활용신청, 담당자 승인(통상 1–2일)
- [OPEN API 활용방법](https://open.law.go.kr/LSO/openApi/openApiManual.do): 목록→본문 링크와 별표 파일 링크
- [공동활용 서비스](https://open.law.go.kr/LSO/information/service.do): 국가법령정보센터와 실시간 연계
- [API 활용가이드 목록](https://open.law.go.kr/LSO/openApi/guideList.do): 현재 공개된 API 분류
