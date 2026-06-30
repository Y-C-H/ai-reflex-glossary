# 사전 게시 도구

원본 노션 페이지:

`https://app.notion.com/p/AI-Glossary-27e25cef1df380cdb04dcf5da693de3a`

페이지 주소는 원본 위치를 식별하기 위한 정보입니다. 자동 동기화 실행에는 해당 데이터베이스를 공유받은 Notion 연결 토큰과 data source ID가 별도로 필요합니다.

## 권장 열

`약어·별칭, 풀네임, 한국어 이름, 검색 키워드, 1초 설명, 상세 설명, 분류, 상태, 안정도, 마지막 검수일, 자동 감지, 면접 답변, 원문 링크`

**검색 키워드**에는 사용자들이 실제로 입력할 법한 다른 언어·철자·띄어쓰기·통칭을 쉼표로 넣습니다.

예시:

| 풀네임 | 한국어 이름 | 검색 키워드 |
|---|---|---|
| Bellman Equation | 벨만 방정식 | Bellman, 벨만, 벨만식 |
| Reinforcement Learning | 강화학습 | reinforcement, 강화 학습 |

## 방법 A — 노션 CSV 변환

```bash
python build_from_csv.py "AI Glossary.csv" -o public/glossary.json
```

기본적으로 `published`, `공개`, `검수 완료` 상태만 내보냅니다. 현재 원본 CSV와 권장 확장 CSV를 모두 지원합니다.

## 게시 전 품질 검사

```bash
python audit_glossary.py public/glossary.json
```

다음을 후보로 표시합니다.

- 풀네임 누락
- `이름 보강 필요` 같은 임시 이름
- 영어 이름이 없을 가능성이 높은 한글 전용 항목
- 중복 표시어
- 대체 검색어가 전혀 없는 항목

## 방법 B — 노션에서 매일 자동 동기화

1. 이 `publisher` 폴더를 GitHub 저장소의 루트로 올립니다.
2. GitHub 저장소의 Pages 배포 소스를 **GitHub Actions**로 설정합니다.
3. Repository secrets에 다음 두 값을 추가합니다.
   - `NOTION_TOKEN`: 노션 연결 토큰
   - `NOTION_DATA_SOURCE_ID`: AI 사전 원본의 data source ID
4. 노션에서 원본 데이터 소스를 해당 연결에 공유합니다.
5. `.github/workflows/notion-pages.yml`이 매일 검수 완료 항목만 읽어 `public/glossary.json`을 배포합니다.
6. 배포된 JSON 주소를 확장 프로그램 설정의 **원격 사전 JSON 주소**에 입력합니다.

토큰은 GitHub Secret에만 있고, Chrome 확장 프로그램이나 공개 JSON에는 포함되지 않습니다.

## 운영 원칙

`후보 → 검토 중 → 검수 완료(또는 공개)` 순서로 관리하십시오. 자동 수집 또는 AI가 작성한 초안은 사람이 풀네임, 번역, 출처, 약어 충돌을 확인한 뒤 공개하는 것을 권장합니다.

## 공개 자료에서 신규 용어 후보 수집

`sources.json`에 검토할 공식 블로그·RSS·Atom 주소를 추가한 뒤 실행합니다.

```json
[
  {"name": "공식 기술 블로그", "url": "https://example.com/feed.xml", "type": "rss"}
]
```

```bash
python discover_candidates.py --sources sources.json --glossary public/glossary.json
```

결과는 `review/candidates.json`에만 저장되고 공식 사전에는 자동 병합되지 않습니다.
