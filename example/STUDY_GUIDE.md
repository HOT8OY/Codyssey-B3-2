# 초심자를 위한 B3-2 미션 완벽 학습 및 구현 가이드

이 문서는 **파이썬 기초 문법(변수, 조건문, 반복문, 함수)만 아는 초심자**가 이번 미션을 처음부터 끝까지 이해하고 직접 구현할 수 있도록 만든 친절한 학습서입니다.

> AI 모델별 최신 REST API 규격(`max_completion_tokens`, `verbosity`, `reasoning_effort`, `thinkingConfig` 등)에 대한 상세 설명은 옆에 있는 **[AI_API_GUIDE.md](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/AI_API_GUIDE.md)** 문서를 함께 참고하세요!

---

## 1. 현재 구현된 코드의 레벨은 어느 정도인가요?

결론부터 말씀드리면 **"초급 ~ 중급 사이 (주니어 개발자 입문 수준)"**입니다.

- **초보자도 쉽게 읽을 수 있는 이유 (문법 수준: 초급)**
  - 복잡한 객체지향 클래스 상속(OOP), 비동기 프로그래밍(`async/await`), 외부 프레임워크를 전혀 쓰지 않았습니다.
  - 오직 **파이썬에 기본으로 내장된 표준 라이브러리**와 **기본 함수(`def`), 조건문(`if`), 반복문(`for`), 문자열 다루기**만으로 작성되어 있어 한 줄씩 따라 읽으며 100% 이해할 수 있습니다.
- **실무/평가에서 좋은 점수를 받는 이유 (구조 수준: 중급)**
  - 한 파일에 모든 코드를 뒤섞지 않고 **역할별로 5개의 파일(모듈)로 분리**했습니다.
  - 인터넷이 끊기거나 API 키가 틀렸을 때 외계어 에러(Traceback)를 뱉으며 죽지 않도록 **예외 처리(`try ~ except`)**와 **출력 후처리 검증 로직**을 갖추었습니다.

---

## 2. 각 파일별 내부 구조 상세 표

전체 프로그램은 5개의 파이썬 파일로 이루어져 있습니다. 각 파일 안에 어떤 함수들이 들어 있고 무엇을 주고받는지 표로 정리했습니다.

### 전체 파일 요약표

| 순서 | 파일명 | 비유 역할 | 핵심 책임 | 사용하는 내장 모듈 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | [`git_collector.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/git_collector.py) | 재료 준비 담당 | `git status`, `git diff` 실행 및 `-safe-mode` 민감정보 마스킹 | `subprocess`, `re`, `os`, `sys` |
| **2** | [`prompts.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/prompts.py) | 주문서 작성 담당 | AI에게 보낼 역할/규칙(System)과 재료(User) 프롬프트 조립 | `typing` |
| **3** | [`ai_client.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/ai_client.py) | 외부 요리사 호출 | 환경변수에서 API Key를 읽고 AI 서버(REST API)와 통신 | `urllib.request`, `json`, `os` |
| **4** | [`validator.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/validator.py) | 품질 검수 담당 | 글자 수 제한(72자/80자) 및 필수 섹션(`Why`/`What`/`How to Test`) 검사·보정 | `re`, `typing` |
| **5** | [`main.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/main.py) | 총괄 매니저 | 터미널 명령어(`commit`, `pr`)와 옵션을 읽어 1~4번을 순서대로 실행 | `argparse`, `sys` |

---

### 파일별 세부 함수 구조표

#### ① [`git_collector.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/git_collector.py) — Git 수집 및 안전 모드 모듈
| 함수 이름 | 입력값 (매개변수) | 반환값 (Return) | 하는 일 |
| :--- | :--- | :--- | :--- |
| `run_git_command(args)` | `args: List[str]`<br>(예: `["status", "--porcelain"]`) | `str` (터미널 출력 결과) | 파이썬 안에서 `git ...` 명령어를 실행하고 결과 텍스트를 돌려줍니다. |
| `check_git_root_directory()` | 없음 | 없음 (`None`) | 현재 폴더가 Git 저장소가 맞는지 확인하고, 아니면 에러 출력 후 종료합니다. |
| `get_current_branch()` | 없음 | `str` (예: `"main"`) | 현재 작업 중인 Git 브랜치 이름을 가져옵니다. |
| `collect_git_changes()` | 없음 | `(changed_files, diff_text)` | 변경된 파일 이름 리스트와 상세 코드 변경점(`diff`) 문자열을 묶어서 반환합니다. |
| `apply_safe_mode(...)` | `changed_files`, `diff_text`, `max_files=10`, `max_lines=200` | `(safe_files, masked_diff)` | 이메일·API 키를 `[MASKED_*]`로 가리고, 파일 10개·200줄까지만 잘라냅니다. |

#### ② [`prompts.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/prompts.py) — 프롬프트 생성 모듈
| 함수 이름 | 입력값 (매개변수) | 반환값 (Return) | 하는 일 |
| :--- | :--- | :--- | :--- |
| `build_commit_prompt(...)` | `changed_files`, `diff_text` | `(system_prompt, user_prompt)` | 커밋 메시지 규칙(제목 1줄 72자 이내 + 불릿 본문)이 담긴 프롬프트를 만듭니다. |
| `build_pr_prompt(...)` | `branch_name`, `changed_files`, `diff_text` | `(system_prompt, user_prompt)` | PR 규칙(제목 80자 이내 + `## Why`, `## What`, `## How to Test` + 불릿) 프롬프트를 만듭니다. |

#### ③ [`ai_client.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/ai_client.py) — AI REST API 통신 모듈
| 함수 이름 | 입력값 (매개변수) | 반환값 (Return) | 하는 일 |
| :--- | :--- | :--- | :--- |
| `get_api_key()` | 없음 | `str` (API 키 문자열) | `AI_API_KEY` 환경변수를 읽어오며, 설정되지 않았으면 안내 문구를 출력하고 종료합니다. |
| `is_openai_reasoning_or_gpt5_plus(model)` | `model: str` | `bool` (`True`/`False`) | 모델이 `gpt-5`, `gpt-6`, `o1`, `o3`, `o4` 등 최신 추론 모델인지 확인합니다. |
| `call_ai_api(...)` | `system_prompt`, `user_prompt`, `model`, `temperature`, `max_tokens` | `str` (AI가 생성한 텍스트) | OpenAI / Gemini / Claude 중 알맞은 서버로 HTTP POST 요청을 보내고 응답을 추출합니다. |

#### ④ [`validator.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/validator.py) — 출력 검증 및 후처리 모듈
| 함수 이름 | 입력값 (매개변수) | 반환값 (Return) | 하는 일 |
| :--- | :--- | :--- | :--- |
| `strip_markdown_code_fence(text)` | `text: str` | `str` | AI가 답변 위아래에 붙인 ` ``` ` 마크다운 기호를 깔끔하게 제거합니다. |
| `validate_and_refine_commit(...)` | `raw_text`, `changed_files` | `str` (완성된 커밋 메시지) | 제목이 72자를 넘으면 자르고, 본문에 불릿(`- `)이 없으면 자동으로 보충합니다. |
| `validate_and_refine_pr(...)` | `raw_text`, `changed_files` | `(pr_title, pr_body)` | PR 제목을 80자로 제한하고, `Why` / `What` / `How to Test` 섹션이나 불릿이 빠졌으면 채워 넣습니다. |

#### ⑤ [`main.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/main.py) — 메인 실행 파일
| 함수 이름 | 입력값 (매개변수) | 반환값 (Return) | 하는 일 |
| :--- | :--- | :--- | :--- |
| `build_arg_parser()` | 없음 | `ArgumentParser` | `commit`/`pr` 명령어와 `-model`, `-temperature`, `-max-tokens`, `-safe-mode` 옵션을 정의합니다. |
| `main()` | 없음 | 없음 (`None`) | 프로그램의 시작점으로, 위 1~4번 모듈의 함수들을 순서대로 호출해 결과를 화면에 찍어줍니다. |

---

## 3. 초심자가 자주 헷갈리는 실전 지식 완벽 보충

### 보충 ① API KEY 환경변수 등록은 어떻게 하나요?

#### Q. 왜 코드에 그냥 적으면 안 되고 '환경변수'에 등록하나요?
코드 안에 `api_key = "sk-abc1234..."`라고 적고 `git push`를 하면, 전 세계 누구나 내 API 키를 훔쳐서 내 돈(크레딧)으로 AI를 마음껏 쓸 수 있습니다. 그래서 **코드는 껍데기(`os.getenv("AI_API_KEY")`)만 만들어 두고, 실제 키 값은 내 컴퓨터(터미널)의 비밀 서랍장(환경변수)에 넣어두는 것**입니다.

#### 방법 A: 현재 열린 터미널 창에서만 임시로 등록하기 (가장 간편)
터미널에 아래 명령어를 입력합니다. (주의: `=` 양옆에 띄어쓰기가 없어야 합니다!)

```bash
# macOS / Linux (zsh, bash)
export AI_API_KEY="여기에_발급받은_진짜_API_키_입력"

# 잘 들어갔는지 확인하기 (입력한 키가 화면에 출력되면 성공!)
echo $AI_API_KEY
```
> **주의**: 이 방식은 **터미널 창을 닫으면 사라집니다.** 새 터미널 창을 열었다면 다시 `export ...`를 입력해야 합니다.

#### 방법 B: 터미널을 껐다 켜도 계속 유지되게 영구 등록하기 (macOS 기준)
매번 `export` 치기가 귀찮다면, 터미널이 켜질 때마다 자동으로 읽는 설정 파일(`~/.zshrc`)에 한 줄을 추가하면 됩니다.

```bash
# 1. 설정 파일 맨 아래에 환경변수 등록 명령어를 추가합니다.
echo 'export AI_API_KEY="여기에_발급받은_진짜_API_키_입력"' >> ~/.zshrc

# 2. 방금 수정한 설정 파일을 즉시 적용합니다.
source ~/.zshrc

# 3. 잘 등록되었는지 확인합니다.
echo $AI_API_KEY
```

#### (참고) Windows에서 실행하는 경우
- **PowerShell**: `$env:AI_API_KEY="여기에_발급받은_API_키"` (확인: `echo $env:AI_API_KEY`)
- **CMD (명령 프롬프트)**: `set AI_API_KEY="여기에_발급받은_API_키"`

---

### 보충 ② 다른 레포지토리(다른 프로젝트 폴더)에서 이 도구를 쓰려면 어떻게 하나요?

미션의 **보너스 과제 1번**(*"이전에 수행했던 미션 GitHub 리포지토리에 적용하여 PR 1건 완성하기"*)이나 평소에 내가 개발하는 다른 프로젝트에서 이 도구를 쓰고 싶을 때 어떻게 해야 할까요?

#### 핵심 원리 이해하기
`subprocess.run(["git", "status"])`는 **`main.py` 파일이 저장된 폴더가 아니라, 내가 지금 터미널에서 서 있는 위치(`pwd`, 현재 작업 디렉토리)의 Git 상태**를 읽어옵니다!

따라서 **"분석하고 싶은 다른 프로젝트 폴더로 먼저 이동(`cd`)한 상태에서, 우리 `main.py`의 경로를 불러서 실행"**하면 됩니다.

#### 방법 1: 다른 폴더로 이동(`cd`) 후 `main.py`의 절대 경로로 실행하기
예를 들어 내 다른 프로젝트가 `/Users/내이름/my-other-project`에 있다면:

```bash
# 1. 분석하고 싶은 다른 Git 프로젝트 폴더로 이동합니다.
cd /Users/내이름/my-other-project

# 2. 그 자리에서 우리 도구의 경로를 지정해 실행합니다!
python3 /Users/4321qwaszx9029/Codyssey-B3-2/example/main.py commit
python3 /Users/4321qwaszx9029/Codyssey-B3-2/example/main.py pr -safe-mode
```
이렇게 하면 `my-other-project`의 `git status`와 `git diff`를 읽어서 커밋 메시지와 PR 초안을 만들어 줍니다!

#### 방법 2 (실무 꿀팁): `alias`(단축 명령어)로 등록해서 어디서든 `ai-git`으로 쓰기
매번 긴 경로(`/Users/.../example/main.py`)를 치기 번거롭다면, `~/.zshrc`에 별칭(`alias`)을 하나 등록해 보세요.

```bash
# 1. ~/.zshrc에 'ai-git'이라는 단축 명령어 등록
echo 'alias ai-git="python3 /Users/4321qwaszx9029/Codyssey-B3-2/example/main.py"' >> ~/.zshrc
source ~/.zshrc

# 2. 이제 컴퓨터의 어느 Git 프로젝트 폴더에 가서든 아래처럼 짧게 쓸 수 있습니다!
cd /Users/내이름/아무_프로젝트_폴더
ai-git commit
ai-git pr -temperature 0.2
```

---

### 보충 ③ `subprocess` 사용법과 Git 명령어 옵션 완전 정복

#### 1) `subprocess.run()`의 옵션들은 각각 무슨 뜻인가요?
[`git_collector.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/git_collector.py#L27-L34)에 있는 아래 코드를 하나씩 뜯어봅시다.

```python
result = subprocess.run(
    ["git"] + args,       # 왜 문자열 "git status"가 아니라 리스트 ["git", "status"]로 넣나요?
    capture_output=True,  # 화면에 바로 출력하지 말고 result 변수에 담아라!
    text=True,            # 바이트(b'...')가 아니라 문자열(str)로 변환해라!
    encoding="utf-8",     # 한글 파일명이나 한글 주석이 깨지지 않게 UTF-8로 읽어라!
    errors="replace",     # 혹시 이상한 특수문자가 있어도 에러 내지 말고 '?'로 바꿔서 읽어라!
    check=False,          # 에러가 나도 파이썬이 혼자 죽지 않게 해라! (아래에서 우리가 직접 검사함)
)
```

- **Q. 왜 `"git status"`처럼 한 줄로 안 쓰고 `["git", "status"]`처럼 띄어쓰기 단위로 쪼갠 리스트를 쓰나요?**
  - 보안과 정확성 때문입니다. 리스트로 넘기면 운영체제가 첫 번째 요소를 '실행할 프로그램(`git`)', 나머지 요소들을 '그 프로그램에 넘길 옵션들'로 정확히 인식하여 파일 이름에 공백이 있거나 특수문자가 있어도 안전하게 실행됩니다.
- **`result` 변수 안에는 무엇이 들어 있나요?**
  1. `result.returncode`: 명령어 성공 여부 숫자입니다. **`0`이면 성공**, `1`이나 `128` 등 **`0`이 아니면 에러**입니다.
  2. `result.stdout`: 성공했을 때 화면에 나온 결과 글자입니다. (우리가 필요한 `status`, `diff` 결과!)
  3. `result.stderr`: 실패했을 때 나온 에러 메시지 글자입니다. (예: `fatal: not a git repository`)

#### 2) 코드에서 사용한 Git 명령어와 옵션 총정리

| 코드에서 실행한 명령어 | 일반 명령어와의 차이 및 옵션 의미 | 출력 예시 |
| :--- | :--- | :--- |
| `git rev-parse --show-toplevel` | 현재 속한 Git 저장소의 **최상위 루트 폴더 경로**를 알려줍니다. Git 저장소가 아니면 에러가 납니다. | `/Users/.../Codyssey-B3-2` |
| `git branch --show-current` | 별표(`*`)나 다른 브랜치 목록 없이 **현재 내가 있는 브랜치 이름 딱 하나만** 깔끔하게 출력합니다. | `main` 또는 `feature/login` |
| `git status --porcelain -uall` | - `--porcelain`: 사람용 설명 문구를 다 빼고 **앞 2글자(상태) + 공백 + 파일명** 형태로만 출력해 파이썬으로 자르기(`line[3:]`) 아주 쉽습니다.<br>- `-uall`: 새로 만든 폴더 안의 파일들까지 빠짐없이 낱개 파일로 다 보여줍니다. | ` M main.py` (수정됨)<br>`A  new.py` (추가됨)<br>`?? test.py` (추적 안 됨) |
| `git diff` | 아직 `git add`를 하지 않은(Unstaged) 수정 내용을 보여줍니다. | `+ 추가된 코드 줄`<br>`- 삭제된 코드 줄` |
| `git diff --cached` | 이미 `git add`를 해서 커밋 대기 중인(Staged) 수정 내용을 보여줍니다. (`--staged`와 완전히 같은 뜻입니다.) | `+ 추가된 코드 줄`<br>`- 삭제된 코드 줄` |

---

### 보충 ④ `argparse` 명령어 옵션은 어떻게 동작하나요?

[`main.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/main.py#L29-L68)에서 터미널 옵션을 만드는 방법입니다.

| 구분 | 코드 작성 예시 | 터미널 입력 예시 | 파이썬에서 꺼내 쓰는 법 | 특징 설명 |
| :--- | :--- | :--- | :--- | :--- |
| **위치 인자**<br>(앞에 `-` 없음) | `parser.add_argument("command", choices=["commit", "pr"])` | `python main.py commit` | `args.command`<br>(`"commit"`) | 생략할 수 없는 **필수 입력값**입니다. `choices`에 없는 단어를 치면 자동으로 사용법을 안내하고 막아줍니다. |
| **값 입력 옵션**<br>(앞에 `-` 붙음) | `parser.add_argument("-temperature", type=float, default=0.3)` | `python main.py commit -temperature 0.5` | `args.temperature`<br>(`0.5`) | 생략하면 `default` 값(`0.3`)이 들어가고, 입력하면 `type=float`(소수)로 자동 변환해 줍니다. |
| **스위치(플래그) 옵션**<br>(`store_true`) | `parser.add_argument("-safe-mode", action="store_true")` | `python main.py commit -safe-mode` | `args.safe_mode`<br>(`True` 또는 `False`) | 뒤에 숫자나 글자를 적지 않고 **옵션 이름만 적으면 켜지는(`True`) 전원 스위치**입니다. 안 적으면 `False`가 됩니다. (`-safe-mode`의 하이픈 `-`은 변수명에서 자동으로 밑줄 `_`인 `args.safe_mode`로 바뀝니다!) |

---

## 4. 백지에서부터 직접 만들어보는 5단계 구현 순서 (단계별 테스트 방법 포함)

처음부터 5개 파일을 다 만들려고 하면 어디서 에러가 났는지 찾기 어렵습니다. **반드시 아래 순서대로 파일 하나를 만들 때마다 바로 테스트하며 조립하세요.**

> **팁**: 각 파일 맨 아래에 `if __name__ == "__main__":` 블록을 임시로 적어두거나, 터미널에서 `python3 -c "..."` 한 줄 명령어로 해당 파일의 함수만 단독 테스트할 수 있습니다.

---

### Step 1. Git 변경 사항 가져오는 [`git_collector.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/git_collector.py) 먼저 만들기
1. `run_git_command()`, `check_git_root_directory()`, `get_current_branch()`, `collect_git_changes()` 함수를 작성합니다.
2. 이어서 `apply_safe_mode()` 함수를 추가해 줄 수 자르기(`[:200]`)와 정규식 마스킹(`re.sub`)을 구현합니다.

- **Step 1 간단 테스트 방법 (터미널에서 실행)**
  ```bash
  # 1) 현재 브랜치, 변경된 파일 목록, diff 길이가 잘 수집되는지 확인
  python3 -c "from git_collector import get_current_branch, collect_git_changes; files, diff = collect_git_changes(); print('브랜치:', get_current_branch()); print('파일목록:', files); print('diff 앞부분:\n', diff[:200])"

  # 2) 안전 모드(마스킹)가 가짜 이메일/API 키를 잘 가리는지 확인
  python3 -c "from git_collector import apply_safe_mode; f, d = apply_safe_mode(['a.py'], 'email: test@naver.com, key: sk-1234567890abcdef12345'); print(d)"
  ```
  - **정상 확인 기준**: 첫 번째 명령에서 내 프로젝트의 변경 파일 리스트가 출력되고, 두 번째 명령에서 `[MASKED_EMAIL]`과 `[MASKED_API_KEY]`로 바뀌어 출력되면 성공입니다!

---

### Step 2. AI 서버와 통신하는 [`ai_client.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/ai_client.py) 만들기
1. `get_api_key()` 함수를 만들어 환경변수 `AI_API_KEY`를 읽어옵니다.
2. `call_ai_api()` 함수를 작성해 REST API 요청 전송 및 예외 처리를 구현합니다.

- **Step 2 간단 테스트 방법 (터미널에서 실행)**
  ```bash
  # 1) API 키가 없을 때 에러 안내가 잘 뜨는지 테스트 (일시적으로 빈 값 전달)
  AI_API_KEY="" python3 -c "from ai_client import get_api_key; get_api_key()"

  # 2) 실제 API 키를 등록한 뒤 짧은 인사말이 잘 돌아오는지 테스트
  export AI_API_KEY="발급받은_진짜_API_KEY"
  python3 -c "from ai_client import call_ai_api; print(call_ai_api('너는 친절한 개발 도우미야.', '한 줄로 짧게 인사해줘.', 'gpt-4o-mini', 0.3, 100))"
  ```
  - **정상 확인 기준**: 1번에서 `[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.`가 출력되고, 2번에서 AI의 한 줄 인사말이 터미널에 찍히면 성공입니다! (Gemini 키라면 `'gpt-4o-mini'` 대신 `'gemini-2.5-flash'` 입력)

---

### Step 3. 프롬프트 조립기 [`prompts.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/prompts.py) 만들기
1. `build_commit_prompt()`와 `build_pr_prompt()` 함수를 만듭니다.
2. 미션 문서에서 요구하는 규칙(커밋 제목 1줄 + 불릿 요약 / PR 제목 + `Why`, `What`, `How to Test` 섹션)을 System 프롬프트 문자열에 꼼꼼히 적어줍니다.

- **Step 3 간단 테스트 방법 (터미널에서 실행)**
  ```bash
  # 가짜 파일 목록과 diff를 넣었을 때 System / User 프롬프트가 잘 합쳐지는지 확인
  python3 -c "from prompts import build_commit_prompt; sys_p, usr_p = build_commit_prompt(['main.py'], '+ print(1)'); print('=== SYSTEM ===\n', sys_p); print('=== USER ===\n', usr_p)"
  ```
  - **정상 확인 기준**: 출력 규칙이 적힌 System 프롬프트와 `[변경된 파일 목록]`, `[Git Diff 내용]`이 합쳐진 User 프롬프트가 깨짐 없이 출력되면 성공입니다!

---

### Step 4. 결과 검수기 [`validator.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/validator.py) 만들기
1. `validate_and_refine_commit()` 함수에서 제목 길이(72자 제한)와 불릿 포함 여부를 체크합니다.
2. `validate_and_refine_pr()` 함수에서 제목 길이(80자 제한)와 `## Why`, `## What`, `## How to Test` 섹션 및 불릿이 빠지지 않았는지 검사·보충하는 코드를 작성합니다.

- **Step 4 간단 테스트 방법 (API 호출 없이 가짜 텍스트로 검증 로직만 테스트)**
  ```bash
  # 1) 커밋 제목이 72자를 넘고 불릿이 없을 때 자동으로 잘리고 불릿이 붙는지 확인
  python3 -c "from validator import validate_and_refine_commit; print(validate_and_refine_commit('feat: ' + '가'*80, ['main.py']))"

  # 2) PR 본문에 Why/What/How to Test 섹션이 빠져 있을 때 자동으로 채워 주는지 확인
  python3 -c "from validator import validate_and_refine_pr; title, body = validate_and_refine_pr('TITLE: 테스트 PR\n아무 내용 없음', ['main.py']); print('제목:', title); print('본문:\n', body)"
  ```
  - **정상 확인 기준**: 1번에서 제목 끝이 `...`으로 72자에 맞춰 잘리고 아래에 `- 변경된 주요 파일: main.py`가 자동 추가되며, 2번에서 `## Why`, `## What`, `## How to Test`와 불릿이 자동으로 생성되면 성공입니다!

---

### Step 5. 매니저 파일 [`main.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/main.py)에서 하나로 합치기
1. `build_arg_parser()`로 `commit` / `pr` 명령어와 `-model`, `-temperature`, `-max-tokens`, `-safe-mode` 옵션을 등록합니다.
2. `main()` 함수 안에서 앞서 만든 1~4번 파일의 함수들을 순서대로 호출하고, 구분선(`--- Commit Message ---` 등)과 함께 출력하면 완성입니다!

- **Step 5 최종 통합 테스트 방법 (터미널에서 실행)**
  ```bash
  # 1) 도움말(-h) 옵션들이 정상 등록되었는지 확인
  python3 main.py --help

  # 2) 커밋 메시지 생성 전체 흐름 실행
  python3 main.py commit

  # 3) PR 초안 생성 + 안전 모드 및 옵션 변경 실행
  python3 main.py pr -temperature 0.2 -max-tokens 700 -safe-mode
  ```

---

## 5. 과제 목표(셀프 체크 / 평가 대비) 핵심 Q&A

미션의 **[3. 과제 목표]**에 있는 5가지 질문을 스스로 설명할 수 있는지 확인해 보세요.

1. **Q. AI API를 REST API 방식으로 연동하는 전체 흐름은 무엇인가요?**
   - **A.** 환경변수에서 API Key를 불러와 HTTP 요청 헤더(`Authorization`)에 담고, 프롬프트와 파라미터를 JSON 형태의 Body로 구성해 POST 요청을 보냅니다. 응답을 받으면 JSON을 파싱해 텍스트를 추출하고, 네트워크 단절(`URLError`)이나 인증 실패·한도 초과(`HTTPError` 401/429) 같은 예외를 처리합니다.
2. **Q. `temperature`와 `max_tokens`(`max_completion_tokens`)는 결과 품질에 어떤 영향을 주나요?**
   - **A.** `temperature`는 생성 문장의 무작위성(창의성)을 조절합니다. 커밋/PR처럼 정해진 템플릿과 사실 기반 요약이 중요할 때는 낮게(`0.2~0.3`) 설정해야 일관된 품질이 나옵니다. `max_tokens`(`max_completion_tokens`)는 생성할 최대 토큰 길이를 제한하여 불필요하게 긴 응답과 과도한 API 비용을 방지합니다.
3. **Q. `git status`, `git diff`를 프로그램 입력으로 연결하는 흐름은 어떻게 되나요?**
   - **A.** 파이썬 `subprocess.run()`으로 두 명령어를 실행해 표준 출력(`stdout`)을 문자열로 캡처한 뒤, 변경 사항이 없으면 즉시 종료하고, 변경 사항이 있으면 파일 목록과 diff 텍스트를 프롬프트에 삽입해 AI에게 전달합니다.
4. **Q. 원하는 양식의 커밋/PR 요약을 얻기 위해 프롬프트를 어떻게 설계했나요?**
   - **A.** System 프롬프트에 역할(숙련된 엔지니어)과 명확한 출력 제약 조건(Conventional Commits 제목, 글자 수 제한, PR의 `## Why`, `## What`, `## How to Test` 헤더 및 불릿 필수)을 명시하고, User 프롬프트에 브랜치명·변경 파일 목록·diff 컨텍스트를 구조화하여 전달했습니다.
5. **Q. 생성된 텍스트를 코드로 한 번 더 검증하고 다듬는(후처리) 이유는 무엇인가요?**
   - **A.** AI 모델은 확률적으로 문장을 생성하므로 프롬프트로 지시하더라도 간혹 글자 수를 초과하거나 마크다운 코드 블록(` ``` `)을 포함하거나 특정 섹션을 누락할 수 있습니다. 이를 파이썬 후처리 코드로 검증·보정하면 추가 API 재호출 비용 없이도 실무 규칙을 100% 만족시킬 수 있습니다.
