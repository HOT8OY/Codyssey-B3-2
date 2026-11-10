# AI 기반 Git 커밋 메시지 / PR 초안 자동 생성기 (학습용 예제)

`git status`와 `git diff` 결과를 수집하여 AI API(OpenAI / Google Gemini 호환)를 호출하고, 실무 규칙에 맞는 **커밋 메시지**와 **Pull Request(PR) 제목/본문 초안**을 터미널에 자동으로 출력해 주는 Python CLI 도구입니다.

---

## 1. 설치 및 실행 방법

### 요구 사항
- **Python 3.10 이상** (Python 3.9+ 호환)
- **Git** 설치 및 초기화된 저장소 (`git init`)
- 파이썬 표준 라이브러리(`subprocess`, `urllib.request`, `argparse`, `json`, `re`, `os`)만 사용하여 별도의 외부 패키지 설치(`pip install`) 없이 바로 실행됩니다.

### 프로젝트 파일 구조
```text
example/
├── main.py           # CLI 진입점 및 전체 흐름 제어 (argparse)
├── git_collector.py  # Git 변경 사항(status, diff) 수집 및 안전 모드(-safe-mode) 마스킹
├── prompts.py        # Commit / PR 생성용 System & User 프롬프트 설계
├── ai_client.py      # 환경변수 로드 및 AI REST API(OpenAI / Gemini) 호출·예외 처리
├── validator.py      # 출력 텍스트 길이 제한(72자/80자) 및 필수 섹션/불릿 검증·보정
├── STUDY_GUIDE.md    # 초심자를 위한 개념 설명 및 5단계 구현 가이드
├── AI_API_GUIDE.md   # OpenAI(GPT-5+) / Gemini / Claude 세대별 REST API 파라미터 완벽 가이드
└── README.md         # 프로젝트 사용 설명서
```

### 실행 위치
반드시 **Git이 초기화된 프로젝트 루트 디렉토리**에서 실행해야 합니다.

```bash
# 프로젝트 루트 디렉토리에서 실행
python3 example/main.py --help
```

---

## 2. 환경변수(API Key) 설정 방법

보안을 위해 API Key는 코드에 하드코딩하지 않으며, 반드시 `AI_API_KEY` 환경변수로 설정해야 합니다.
OpenAI API Key(`sk-...`)와 Google Gemini API Key(`AQ.Ab...`)를 모두 자동으로 인식합니다.

```bash
# macOS / Linux (zsh, bash)
export AI_API_KEY="YOUR_API_KEY"
```

환경변수가 설정되지 않은 상태로 실행하면 아래와 같이 안내 메시지가 출력되고 종료됩니다.
```text
[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.
## 예) export AI_API_KEY="YOUR_KEY"
```

---

## 3. 커밋 / PR 생성 명령 사용 예시

### 기본 명령어
```bash
# 1) 커밋 메시지 초안 생성
python3 example/main.py commit

# 2) Pull Request(PR) 제목 및 본문 초안 생성
python3 example/main.py pr
```

### CLI 옵션 활용 (`-model`, `-temperature`, `-max-tokens`, `-safe-mode`)
```bash
# OpenAI GPT-6 모델(gpt-6-luna, gpt-6.1-sol, gpt-6.1-terra, gpt-6-astra) 지정 실행
python3 example/main.py commit -model gpt-6-luna -max-tokens 1500

# Google Gemini 모델(gemini-3.8-flash, gemini-4-argon, gemini-4-carbon) 지정 실행
python3 example/main.py pr -model gemini-4-argon -temperature 0.3

# 안전 모드(-safe-mode)를 켜서 민감정보 마스킹 및 diff 전송량 제한 적용
python3 example/main.py commit -safe-mode
```

| 옵션 | 기본값 | 설명 |
| :--- | :--- | :--- |
| `-model`, `--model` | `gpt-6-luna` | 호출할 AI 모델명 (`AQ.Ab...` 키 사용 시 `gemini-3.8-flash` 자동 전환) |
| `-temperature`, `--temperature` | `0.3` | 결과의 창의성/무작위성 조절 (`0.0`에 가까울수록 일관된 형식 유지) |
| `-max-tokens`, `--max-tokens` | `600` | AI가 생성할 최대 응답 토큰 수 (추론 모델에서는 최소 1500으로 안전 보정) |
| `-safe-mode`, `--safe-mode` | `False` | 민감정보 정규식 마스킹 및 최대 10개 파일 / 200줄까지만 전송 |

---

## 4. 출력 예시

### ① 커밋 메시지 자동 생성 (`commit`)
```text
[INFO] Git status 수집 완료: 2개 파일 변경 감지
[INFO] Git diff 수집 완료: 84줄
[INFO] AI API 요청 중... (model=gpt-4o-mini, temperature=0.3, max_tokens=600)
[DONE] 커밋 메시지 생성 완료 (AI API 호출 횟수: 1회)

--- Commit Message ---
feat: Git 변경 사항 기반 커밋 메시지 및 PR 초안 자동 생성 CLI 구현

- example/main.py, example/README.md 파일 추가 및 사용 가이드 작성
- git status 및 git diff 결과를 수집해 AI 프롬프트 컨텍스트로 전달하는 로직 구현
- 커밋 제목 길이(최대 72자) 및 PR 템플릿(Why/What/How to Test) 검증 후처리 적용
----------------------
```

### ② PR 제목/본문 자동 생성 (`pr`)
```text
[INFO] 현재 브랜치: main
[INFO] Git status 수집 완료: 2개 파일 변경 감지
[INFO] Git diff 수집 완료: 84줄
[INFO] AI API 요청 중... (model=gpt-4o-mini, temperature=0.3, max_tokens=600)
[DONE] PR 초안 생성 완료 (AI API 호출 횟수: 1회)

--- PR Title ---
feat: AI 기반 Git 커밋 메시지 및 PR 초안 자동 생성 도구 추가

--- PR Body ---
## Why
- 반복적인 커밋 메시지와 PR 설명 작성 시간을 단축하고 일관된 문서 품질을 유지하기 위해 자동 생성 도구가 필요했습니다.

## What
- `subprocess`를 활용해 `git status`, `git diff` 결과를 수집하는 함수 구현
- OpenAI 및 Gemini REST API를 호출하고 예외(401, 429, 네트워크 오류)를 처리하는 모듈 작성
- `-safe-mode`를 통한 민감정보 마스킹 및 출력 형식 검증 로직 추가

## How to Test
- 환경변수 설정: `export AI_API_KEY="YOUR_KEY"`
- 커밋 메시지 생성 확인: `python3 example/main.py commit`
- PR 초안 생성 확인: `python3 example/main.py pr`
- 생성된 PR 본문에 Why / What / How to Test 섹션과 불릿이 포함되는지 확인
---------------
```

---

## 5. 주의사항 및 운영 가이드

### 보안 및 민감정보 대응 (`-safe-mode`)
- `git diff`에는 실수로 작성된 API Key, 비밀번호, 개인 이메일 등이 포함될 수 있습니다.
- 외부 AI API로 코드가 전송되기 전에 `-safe-mode` 옵션을 활성화하면 다음 두 가지 보호 조치가 적용됩니다:
  1. **패턴 마스킹**: 이메일 주소(`[MASKED_EMAIL]`), API 토큰(`sk-...`, `AIza...`, `ghp_...` 등 -> `[MASKED_API_KEY]`), 시크릿 변수 할당문(`[MASKED_SECRET]`)을 정규표현식으로 자동 치환합니다.
  2. **전송 범위 제한**: 변경된 파일은 **최대 10개**, diff 텍스트는 **최대 200줄**까지만 잘라서 전송합니다.

### 비용 및 요청 횟수 제한 권장 사용법
- 과도한 API 호출 비용을 방지하기 위해 `commit` 및 `pr` 명령은 **1회 실행당 정확히 1번만 AI API를 호출**하도록 설계되어 있으며, 완료 로그에 호출 횟수를 표시합니다.
- 출력 형식 검증(제목 길이 제한, 필수 섹션/불릿 누락 보정)은 추가 API 재호출 대신 **파이썬 후처리 로직**으로 수행하여 불필요한 토큰 소모를 막습니다.
- 생성된 문구는 초안이므로, 실제 커밋이나 PR에 반영하기 전 반드시 내용을 검토한 뒤 사용하세요.

