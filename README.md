# AI 기반 Git 커밋 메시지 / PR 초안 자동 생성기

`git status`와 `git diff` 결과를 수집하여 AI REST API(OpenAI GPT / Google Gemini / Anthropic Claude 호환)를 호출하고, 실무 규칙에 맞는 **커밋 메시지**와 **Pull Request(PR) 제목/본문 초안**을 터미널에 자동으로 출력해 주는 Python CLI 도구입니다.

---

## 1. 설치 및 실행 방법

### 개발 및 실행 환경 요구 사항
- **Python 3.10 이상**
- **Git** 설치 및 초기화된 저장소 (`git init`)
- 파이썬 표준 라이브러리(`subprocess`, `urllib.request`, `argparse`, `json`, `re`, `os`, `sys`)만 사용하여 별도의 외부 패키지 설치(`pip install`) 없이 즉시 실행할 수 있습니다.

### 프로젝트 구조
```text
Codyssey-B3-2/
├── main.py           # CLI 진입점 및 전체 실행 흐름 제어 (argparse)
├── git_collector.py  # Git 변경 사항(status, diff) 수집 및 안전 모드(-safe-mode) 처리
├── prompts.py        # Commit / PR 생성용 System & User 프롬프트 템플릿 조립
├── ai_client.py      # 환경변수(AI_API_KEY) 로드 및 AI REST API 호출·예외 처리
├── validator.py      # 출력 텍스트 길이 제한(72자/80자) 및 필수 섹션/불릿 검증·후처리
└── README.md         # 프로젝트 사용 가이드 문서
```

### 설치 및 실행 위치
1. 저장소를 클론(또는 다운로드)하고 **Git이 초기화된 프로젝트 루트 디렉토리**로 이동합니다.
   ```bash
   git clone <REPOSITORY_URL>
   cd Codyssey-B3-2
   ```
2. 도움말 명령어로 정상 동작 여부를 확인합니다.
   ```bash
   python3 main.py --help
   ```

---

## 2. 환경변수(API Key) 설정 방법

보안을 위해 API Key는 소스 코드에 하드코딩하지 않으며, 실행 전 반드시 `AI_API_KEY` 환경변수로 설정해야 합니다.  
OpenAI API Key(`sk-...`), Google Gemini API Key(`AQ.Ab...` / `AIza...`), Anthropic Claude API Key(`sk-ant-...`)를 자동으로 판별하여 연동합니다.

### macOS / Linux (zsh, bash)
```bash
export AI_API_KEY="YOUR_API_KEY"
```

### Windows (PowerShell)
```powershell
$env:AI_API_KEY="YOUR_API_KEY"
```

> **참고**: 환경변수가 설정되지 않은 상태에서 실행하면 아래와 같은 오류 안내 메시지를 출력하고 안전하게 종료됩니다.
> ```text
> [ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.
> ## 예) export AI_API_KEY="YOUR_KEY"
> ```

---

## 3. 커밋 / PR 생성 명령 사용 예시

### 기본 실행 명령어
```bash
# 1) 변경 사항 기반 커밋 메시지 초안 생성
python3 main.py commit

# 2) 변경 사항 기반 Pull Request(PR) 제목 및 본문 초안 생성
python3 main.py pr
```

### CLI 옵션 활용 예시 (`-model`, `-temperature`, `-max-tokens`, `-safe-mode`)
```bash
# 사용할 AI 모델 및 최대 토큰 수 지정 (Google Gemini 사용 예시)
python3 main.py commit -model gemini-3.8-flash -max-tokens 1500

# OpenAI GPT-6 모델 및 temperature 파라미터 지정
python3 main.py pr -model gpt-6-luna -temperature 0.3

# 안전 모드(-safe-mode)를 활성화하여 민감정보 마스킹 및 diff 전송량 제한 적용
python3 main.py commit -safe-mode
```

### 지원 CLI 옵션 표
| 옵션 | 기본값 | 설명 |
| :--- | :--- | :--- |
| `commit` / `pr` | (필수 위치 인자) | `commit`: 커밋 메시지 초안 생성 / `pr`: PR 제목 및 본문 초안 생성 |
| `-model`, `--model` | `gpt-6-luna` | 호출할 AI 모델 이름 (`AQ.`로 시작하는 Gemini 키 사용 시 `gemini-3.8-flash` 자동 호환) |
| `-temperature`, `--temperature` | `0.3` | 생성 결과의 무작위성/창의성 조절 (`0.0` ~ `1.0`) |
| `-max-tokens`, `--max-tokens` | `600` | AI 응답의 최대 토큰 수 제한 (추론 모델 호환을 위해 내부적으로 충분한 토큰 확보) |
| `-safe-mode`, `--safe-mode` | `False` | diff 내 민감정보(API Key, 이메일 등) 마스킹 및 최대 10개 파일 / 200줄 제한 |

---

## 4. 출력 예시 (커밋 메시지 / PR 본문 예시)

### ① 커밋 메시지 자동 생성 예시 (`python3 main.py commit`)
```text
[INFO] Git status 수집 완료: 5개 파일 변경 감지
[INFO] Git diff 수집 완료: 142줄
[INFO] AI API 요청 중...(model=gemini-3.8-flash, temperature=0.3, max_tokens=600)
[DONE] 커밋 메시지 생성 완료 (AI API 호출 횟수: 1회)

--- Commit Message ---
feat: Git 변경 사항 기반 커밋 메시지 및 PR 초안 자동 생성 CLI 구현

- git_collector.py, ai_client.py, validator.py 등 핵심 모듈 구현
- git status 및 git diff 결과를 수집해 AI 프롬프트 컨텍스트로 전달하도록 연결
- 커밋 제목 길이 제한(최대 72자) 및 Conventional Commits 규칙 검증 로직 적용
----------------------
```

### ② PR 제목/본문 자동 생성 예시 (`python3 main.py pr`)
```text
[INFO] 현재 브랜치: main
[INFO] Git status 수집 완료: 5개 파일 변경 감지
[INFO] Git diff 수집 완료: 142줄
[INFO] AI API 요청중(model=gemini-3.8-flash, temperature=0.3, max_tokens=600)
[DONE] PR 초안 생성 완료 (AI API 호출 횟수: 1회)

--- PR Title ---
feat: AI 기반 Git 커밋 메시지 및 PR 초안 자동 생성 CLI 도구 구현

--- PR Body ---
## Why
- 팀 협업 시 반복적인 커밋 메시지와 PR 설명 작성에 소요되는 시간을 줄이고, 일관된 문서 양식을 유지하기 위해 자동 생성 도구를 구현했습니다.

## What
- `git status`, `git diff` 명령 실행 결과를 수집하고 `-safe-mode`로 민감정보를 보호하는 `git_collector.py` 구현
- 환경변수(`AI_API_KEY`) 기반 REST API 요청 및 HTTP 예외 처리를 담당하는 `ai_client.py` 구현
- 커밋 메시지 및 PR 템플릿(`Why`, `What`, `How to Test`) 형식과 길이 규칙을 검증·보정하는 `validator.py` 추가

## How to Test
- 환경변수 설정: `export AI_API_KEY="YOUR_KEY"`
- 커밋 메시지 생성 확인: `python3 main.py commit`
- PR 초안 생성 확인: `python3 main.py pr`
- 출력된 PR 본문에 `Why`, `What`, `How to Test` 섹션 헤더와 각 섹션의 불릿(`- `)이 포함되는지 확인
---------------
```

### ③ 예외 및 안내 상황 출력 예시
- **변경 사항이 없는 경우**
  ```text
  [INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다.
  ```
- **Git 저장소가 아닌 폴더에서 실행한 경우**
  ```text
  [ERROR] 현재 디렉토리는 Git 저장소가 아닙니다. Git이 초기화된 프로젝트에서 실행해 주세요.
  ```

---

## 5. 주의사항 및 운영 가이드

### 1) 민감정보 포함 가능성과 대응 (`-safe-mode` 안내)
- `git diff` 결과에는 코드에 실수로 포함된 API Key, 토큰, 비밀번호, 개인 이메일 등 민감정보가 들어 있을 수 있습니다.
- 외부 AI API로 변경 내용을 전송하기 전 `-safe-mode` 옵션을 사용하면 다음 두 가지 보호 정책이 자동으로 적용됩니다:
  1. **정규표현식 기반 민감정보 마스킹**:
     - 이메일 주소 → `[MASKED_EMAIL]`
     - 주요 API Key 패턴(`sk-...`, `AIza...`, `AQ.Ab...`, `ghp_...` 등) → `[MASKED_API_KEY]`
     - 시크릿 변수 할당문(`api_key = "..."`, `password = "..."`, `secret = "..."` 등) → `[MASKED_SECRET]`
  2. **전송 범위 제한**:
     - 변경된 파일 목록은 **최대 10개 파일**까지만 포함합니다.
     - `git diff` 텍스트는 **최대 200줄**까지만 잘라서 전송하여 불필요한 코드 유출과 과도한 토큰 사용을 방지합니다.

### 2) 비용/요청 횟수 제한 및 권장 사용법
- **1회 실행당 단일 API 호출 원칙**: 과도한 API 호출 비용이 발생하지 않도록 `commit`과 `pr` 명령은 **1회 실행 시 AI API를 딱 1번만 호출**하며, 완료 시 `[DONE] ... (AI API 호출 횟수: 1회)` 로그를 출력합니다.
- **로컬 후처리 기반 검증**: 제목 글자 수 제한(커밋 제목 최대 72자, PR 제목 최대 80자)이나 필수 섹션(`## Why`, `## What`, `## How to Test`) 및 불릿 누락 보정은 API를 재호출하지 않고 `validator.py`의 파이썬 후처리 로직으로 즉시 교정하여 비용을 절약합니다.
- **초안 검토 후 반영**: 본 도구는 원격 저장소에 자동으로 `git push` 하거나 GitHub PR을 직접 등록하지 않고 **터미널에 초안 텍스트를 출력**하는 역할만 수행합니다. 생성된 문구는 최종 정답이 아니므로, 반드시 사용자가 내용을 검토하고 다듬은 뒤 실제 커밋 및 PR에 적용하시기 바랍니다.
