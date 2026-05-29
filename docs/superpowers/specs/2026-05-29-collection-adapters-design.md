# Spec: 수집 어댑터 파이프라인 업그레이드 (RSS + 시군 게시판)

날짜: 2026-05-29
대상: `jeonnam-issue-cards`
범위: 1차 — 0+1+2단계 (인프라 + RSS 어댑터 + 시군 게시판 HTML 어댑터)

## 배경 / 문제

현재 `scripts/collect.py`는 하드코딩된 `SAMPLE_ITEMS` 4개만 반환한다. 정작 소스 설정
(`config/news_rss_sources.json`의 전남도청·미디어 RSS, `config/crawler_strategy.json`의
수집 순서 정책)은 갖춰져 있으나 코드가 사용하지 않는다. 파이프라인 뒷단(score → build_specs →
audit → render → qc → send)은 동작하지만 입력이 가짜 데이터다.

이 스펙은 실제 수집 어댑터 프레임워크를 도입해 RSS와 22개 시군 공식 게시판에서 실데이터를
수집하도록 한다.

## 목표

- 공통 인터페이스를 가진 소스 어댑터 프레임워크 도입 (RSS / HTML board / fallback 위임)
- 전남도청 + 미디어 RSS 실수집
- 22개 시군 공식 게시판 HTML 어댑터 (config 기반, 사이트별 selector)
- 22개 지역명 매칭 + PRD 제외 규칙 1차 필터
- 네트워크 비의존 단위/통합 테스트 유지

## 범위 밖 (다음 스펙)

- crawl4ai fallback — crawl4ai는 python 3.9에서 `X | None` 문법 에러로 작동 불가, python 3.10+
  별도 환경 구축이 선행되어야 하므로 3단계 별도 스펙으로 분리한다.
- 22개 시군 각 사이트의 URL/selector 전수 조사는 본 프레임워크 위에서 진행하는 구현 산출물이다.
  (프레임워크와 대표 시군 일부의 동작 검증이 본 스펙의 완료 기준)

## 인프라 제약 (사전 확인 결과)

| 항목 | 상태 | 대응 |
|---|---|---|
| feedparser | 미설치 (시스템·venv 모두) | requirements.txt + venv 설치 |
| requests / bs4 / lxml | bs4 4.14.3·lxml 사용 가능 | requests 설치 확인 |
| crawl4ai | python 3.9에서 import 실패 (3.10+ 필요) | 범위 밖, insane-search로 대체 |
| insane-search 스킬 | 0.4.0 사용 가능 | 차단 페이지 fallback 위임 |
| 전남도청 RSS | 302 후 정상 XML (리다이렉트 추적 필요) | http_client가 -L 동등 추적 |
| 지자체 사이트 | curl 직접 요청에 응답 안 함 (WAF/봇 차단 흔함) | http_client 실패 시 insane-search 위임 |

## 아키텍처

```
scripts/
  http_client.py     # 공통 HTTP: 리다이렉트 추적, UA, 타임아웃, 재시도,
                     #   차단(403/타임아웃) 시 insane-search 위임 hook
  adapters/
    base.py          # SourceAdapter 인터페이스
    rss.py           # RssAdapter (feedparser)
    html_board.py    # HtmlBoardAdapter (requests + bs4, selector 설정 기반)
    registry.py      # config 읽어 어댑터 인스턴스 생성·순회
  collect.py         # registry 순회 → 정규화 → 지역매칭 → 제외필터 → data/raw 저장
tests/
  fixtures/          # 기존 SAMPLE_ITEMS 이전 + RSS/HTML 샘플 페이로드
```

### SourceAdapter 인터페이스 (base.py)

```python
class SourceAdapter:
    source_type: str        # official_city | official_province | national_media_rss | ...
    source_method: str      # rss | html_board | search_fallback
    def fetch(self, date: str) -> list[RawItem]: ...
```

- 각 어댑터는 정규화된 `RawItem`(dict) 리스트를 반환한다.
- 어댑터는 자신의 `source_type`, `trust_tier`, `source_method`를 RawItem에 기록한다.

### RawItem 스키마

```
title:         str
body:          str
url:           str
published_at:  str (YYYY-MM-DD)
source_name:   str
source_type:   str
source_method: str   # rss | html_board | search_fallback | fixture
region:        str | None   # 지역 매칭 결과 (없으면 None → 후속 필터 대상)
trust_tier:    int
```

기존 score.py가 사용하는 필드(title/body/url/published_at/source_name/source_type)는 유지하고
`region`, `trust_tier`, `source_method`를 명시적으로 채운다.

### 소스 레지스트리 (config)

- 기존 `config/news_rss_sources.json` (RSS 소스)을 RssAdapter가 사용한다.
- 시군 게시판은 `config/sources.json`(신규) 또는 동일 파일에 `html_boards` 섹션으로 추가한다.

```jsonc
{
  "html_boards": [
    {
      "region": "목포시",
      "url": "https://.../boardList",
      "list_selector": "table.bbs tr",
      "item": { "title": "td.title a", "url": "td.title a@href",
                "date": "td.date", "date_format": "%Y.%m.%d" },
      "source_type": "official_city",
      "trust_tier": 1
    }
    // 22개 시군 — 구현 시 사이트별 조사해 채움
  ]
}
```

- registry는 config의 rss + html_boards를 읽어 어댑터 목록을 만들고 `crawler_strategy.json`의
  `default_order`(rss → html_board → ...) 순으로 순회한다.

### http_client.py

- requests 기반. 302 리다이렉트 추적, `User-Agent: Mozilla/5.0`, 타임아웃(기본 10s), 재시도(2회).
- 403/타임아웃/빈 응답 등 차단 신호 시 insane-search 위임 hook을 호출한다(인터페이스만 정의,
  실제 위임 구현은 html_board 어댑터에서 사용). 07:00 배달 지연 방지를 위해 페이지 수·시간 캡 적용.

### 지역 매칭 + 제외 규칙 (collect.py 후처리)

- `config/regions.json`의 22개 지역명 사전으로 제목·본문을 매칭해 `region` 채움.
- official_city 어댑터는 출처가 곧 지역이므로 region을 직접 부여.
- RSS(도청·미디어)는 본문 매칭으로 region 부여하고, 매칭 없으면 None → 후속 필터에서 제외 후보.
- PRD 제외 규칙을 1차 필터로 적용: 인사발령, 입찰/계약/구매 공고, 채용 공고, 기관장 동정·사진행사,
  지역명만 우연히 언급된 전국 기사. (키워드/패턴 기반, 보수적으로 — 애매하면 통과시켜 score 단계에 위임)

## 데이터 흐름

```
registry(config) → [RssAdapter, HtmlBoardAdapter×N]
  → 각 adapter.fetch(date) → RawItem[]
  → collect.py: 병합 → 지역매칭 → 제외 1차 필터 → 동일 URL 중복 제거
  → data/raw/YYYY-MM-DD.json  (기존 score.py 입력 경로 유지)
```

중복 처리 책임 분리: collect는 **완전 동일 URL**만 제거(저렴·결정적). 제목 유사도 기반
클러스터링/중복 판정은 기존 score.py의 cluster key 로직이 담당(변경하지 않음).

```
```

## 에러 처리

- 개별 어댑터 실패(네트워크·파싱)는 해당 소스만 건너뛰고 경고 로그를 남긴다(전체 중단 금지).
- 어댑터별 수집 0건도 정상 처리(다른 소스 계속). collect 종료 시 소스별 수집 건수 요약 출력.
- 차단 감지 시 insane-search 위임이 실패해도 파이프라인은 진행(해당 소스만 누락).
- audit_pipeline.py가 source_method 믹스·지역 커버리지를 리포트하므로 수집 품질은 그 단계에서 가시화.

## 테스트

- `tests/fixtures/`: 기존 SAMPLE_ITEMS 이전 + RSS 샘플 XML + HTML board 샘플.
- 어댑터 단위 테스트: RSS XML 파싱, HTML selector 파싱, 날짜 포맷 정규화, 지역 매칭, 제외 필터.
- collect 통합 테스트: 픽스처 소스(네트워크 비의존)로 end-to-end → data/raw 출력 스키마 검증.
- 기존 `tests/test_pipeline.py`의 픽스처 경로를 신규 fixtures로 갱신.

## 완료 기준

- feedparser 설치 + requirements.txt 반영.
- RssAdapter가 전남도청 + 미디어 RSS에서 실제 항목을 수집(리다이렉트 추적 포함).
- HtmlBoardAdapter가 config selector로 게시판 1개 이상에서 실제 항목 수집(대표 시군 검증).
- 지역 매칭·제외 필터가 적용된 RawItem이 data/raw에 저장되고 기존 score.py가 그대로 소비.
- 네트워크 비의존 테스트 전부 통과.
- 22개 시군 config 슬롯은 마련하되, 전수 채움은 후속 작업으로 남김(프레임워크 + 대표 검증이 완료선).
