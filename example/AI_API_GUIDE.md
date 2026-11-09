# 주요 AI REST API 사용법 및 세대별 파라미터 완벽 가이드

이 문서는 OpenAI(GPT), Google(Gemini), Anthropic(Claude) 3대 AI 서비스의 **REST API 호출 구조**와 **최신 모델 세대(GPT-5/5.1+, Gemini 2.5/3+, Claude 4.5/5+)로 넘어오면서 바뀐 핵심 파라미터 규칙**을 초심자도 한눈에 이해할 수 있도록 정리한 레퍼런스입니다.

---

## 1. 한눈에 보는 3대 AI REST API 비교표

| 구분 | OpenAI (GPT 계열) | Google (Gemini 계열) | Anthropic (Claude 계열) |
| :--- | :--- | :--- | :--- |
| **API Key 형태** | `sk-...` 또는 `sk-proj-...` | `AIzaSy...` | `sk-ant-...` |
| **REST 엔드포인트 (URL)** | `https://api.openai.com/v1/chat/completions`<br>*(신규: `/v1/responses`)* | `https://generativelanguage.googleapis.com/v1beta/models/{모델명}:generateContent?key={API_KEY}` | `https://api.anthropic.com/v1/messages` |
| **인증 헤더 (Header)** | `Authorization: Bearer {API_KEY}` | URL 쿼리(`?key=...`) 또는<br>`x-goog-api-key: {API_KEY}` | `x-api-key: {API_KEY}`<br>`anthropic-version: 2023-06-01` |
| **시스템 프롬프트 위치** | `messages` 배열 내<br>`role: "system"` 또는 `"developer"` | 최상위 `systemInstruction` 필드 | 최상위 `system` 필드 |
| **최대 토큰 제한 파라미터** | - 구형: `max_tokens`<br>- **신형(표준): `max_completion_tokens`**<br>- Responses API: `max_output_tokens` | `generationConfig.maxOutputTokens` | `max_tokens` *(필수 입력)* |
| **추론(생각) 깊이 조절** | `reasoning_effort`<br>(`"none"`, `"minimal"`, `"low"`, `"medium"`, `"high"`) | `generationConfig.thinkingConfig`<br>- Gemini 2.5: `thinkingBudget`<br>- Gemini 3+: `thinkingLevel` | `thinking`<br>(`type: "adaptive"` 또는 `"enabled"`, `budget_tokens`) |
| **답변 길이/상세도 스타일** | `verbosity` *(GPT-5 계열 신설)*<br>(`"low"`, `"medium"`, `"high"`) | 프롬프트 지시문으로 제어 | 프롬프트 지시문으로 제어 |

---

## 2. OpenAI API (GPT-4o vs GPT-5 / 5.1+ / o-시리즈) 상세 분석

질문하신 것처럼 **OpenAI는 추론 모델(o1, o3, o4)과 GPT-5 / GPT-5.1 세대부터 요청에 보내는 파라미터 규격이 크게 바뀌었습니다.** 예전 블로그 글에 나오는 구형 코드를 그대로 쓰면 `400 Bad Request` 에러가 발생하는 가장 흔한 원인이 바로 이 부분입니다.

### 핵심 변화 4가지

#### ① `max_tokens` 폐지 $\rightarrow$ `max_completion_tokens`로 변경!
- **과거 (`gpt-3.5-turbo`, 초기 `gpt-4`)**: 화면에 출력되는 글자 수만 제한하는 `max_tokens`를 썼습니다.
- **현재 (`o1`, `o3`, `gpt-5`, `gpt-5.1` 이상)**: 모델이 답변을 내놓기 전에 **내부적으로 생각하는 토큰(Reasoning Tokens)**과 **화면에 보이는 최종 답변 토큰(Visible Output Tokens)**을 합쳐서 제한하는 **`max_completion_tokens`**를 사용해야 합니다.
  - 최신 모델에 구형 `max_tokens`를 보내면 `"Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead."`라는 400 에러가 발생합니다.
  - *(참고)* 만약 새로 도입된 **Responses API (`/v1/responses`)** 엔드포인트를 사용할 때는 이름이 **`max_output_tokens`**로 바뀝니다.
  - **주의점**: 내부 추론 토큰까지 합산되므로, `max_completion_tokens`를 `300`처럼 너무 작게 주면 모델이 생각하다가 토큰을 다 써버려서 정작 화면에는 빈 문자열이 나올 수 있습니다. 최소 `1000 ~ 2000` 이상으로 넉넉히 주거나 `reasoning_effort`를 낮추는 것이 안전합니다.

#### ② `verbosity` 파라미터 신설 (GPT-5 시리즈~)
- 프롬프트에 구구절절 *"짧게 써줘"*, *"자세하게 길게 써줘"*라고 적지 않아도 API 옵션 하나로 답변의 상세도(수다스러움 정도)를 조절할 수 있게 추가된 옵션입니다.
  - `"low"`: 군더더기 설명 없이 핵심 코드나 짧은 요약만 간결하게 출력
  - `"medium"` (기본값): 표준적인 설명 길이
  - `"high"`: 배경 설명, 예시, 상세 해설까지 풍부하게 출력

#### ③ `reasoning_effort` (추론 강도 조절)
- 모델이 답변하기 전에 얼마나 깊이 생각(Chain-of-Thought)할지 결정합니다.
  - 설정 가능 값: `"none"` (또는 `"minimal"`), `"low"`, `"medium"` (기본값), `"high"`
  - 우리 미션처럼 `git diff`를 보고 정해진 양식으로 빠르게 요약하는 작업은 `"low"`나 `"minimal"`로 두면 응답 속도가 훨씬 빠르고 토큰 비용도 아낄 수 있습니다.

#### ④ `role: "developer"` 및 `temperature` 제한 주의!
- **역할 이름 변경**: 기존 `"role": "system"` 대신 **`"role": "developer"`**를 사용하는 것이 최신 표준입니다.
- **`temperature` 에러 주의**: 추론 기능(`reasoning_effort`가 `"low"` 이상)이 켜져 있는 상태에서 `temperature: 0.3`처럼 `1.0`이 아닌 값을 함께 보내면 API가 `400 Bad Request` (`'temperature' is not supported with this model`) 에러를 반환할 수 있습니다.
  - 따라서 최신 추론/GPT-5+ 모델을 호출할 때는 **`temperature` 파라미터를 아예 생략**하거나, 추론을 끄고(`reasoning_effort: "none"`) 사용해야 합니다. ([`ai_client.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/ai_client.py#L106-L125)에 이 분기 처리가 이미 반영되어 있습니다!)

---

### OpenAI 요청 JSON 예시 비교

#### [표준 모델] `gpt-4o-mini`, `gpt-4o` 호출 시
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    { "role": "system", "content": "당신은 숙련된 개발자입니다." },
    { "role": "user", "content": "이 diff를 요약해 주세요." }
  ],
  "temperature": 0.3,
  "max_completion_tokens": 600
}
```

#### [최신 모델] `gpt-5`, `gpt-5.1` 이상 호출 시
```json
{
  "model": "gpt-5.1",
  "messages": [
    { "role": "developer", "content": "당신은 숙련된 개발자입니다." },
    { "role": "user", "content": "이 diff를 요약해 주세요." }
  ],
  "reasoning_effort": "low",
  "verbosity": "medium",
  "max_completion_tokens": 1500
}
```

---

## 3. Google Gemini API 상세 분석

Google Gemini API는 OpenAI와 JSON 모양이 다릅니다. `messages` 대신 `contents`와 `parts`라는 구조를 쓰고, 설정값들은 모두 `generationConfig` 상자 안에 넣습니다.

### 핵심 파라미터 특징

1. **`systemInstruction`**: 시스템 프롬프트를 넣는 전용 칸입니다.
2. **`generationConfig`**:
   - `temperature`: 창의성 조절 (`0.0 ~ 2.0`)
   - `maxOutputTokens`: 최대 출력 토큰 수 (카멜 표기법 주의!)
   - `responseMimeType`: `"application/json"`으로 지정하면 무조건 JSON 형식으로만 답변을 줍니다.
3. **`thinkingConfig` (세대별 차이 주의!)**:
   - **Gemini 2.5 계열 (`gemini-2.5-flash`, `gemini-2.5-pro`)**: 생각할 토큰 예산을 숫자로 직접 지정하는 **`thinkingBudget`**을 사용합니다. (`0`이면 생각 끄기, `-1`이면 자동 조절, `1024`면 최대 1024토큰까지 생각)
   - **Gemini 3 / 최신 세대 모델**: 숫자 예산 대신 단계로 지정하는 **`thinkingLevel`**(`"minimal"`, `"low"`, `"medium"`, `"high"`)을 사용합니다.
   - **주의**: 한 요청에 `thinkingBudget`과 `thinkingLevel`을 동시에 넣으면 `400 Bad Request` 에러가 납니다.

### Google Gemini 요청 JSON 예시
- **URL**: `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=내_API_KEY`

```json
{
  "systemInstruction": {
    "parts": [
      { "text": "당신은 숙련된 개발자입니다." }
    ]
  },
  "contents": [
    {
      "role": "user",
      "parts": [
        { "text": "이 git diff 내용을 바탕으로 커밋 메시지를 작성해 주세요." }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.3,
    "maxOutputTokens": 600,
    "thinkingConfig": {
      "thinkingBudget": 0
    }
  }
}
```

### Google Gemini 응답 JSON에서 텍스트 꺼내기
```python
# 응답 JSON 구조:
# {
#   "candidates": [
#     {
#       "content": {
#         "parts": [ { "text": "feat: 로그인 기능 추가..." } ]
#       }
#     }
#   ]
# }
answer = data["candidates"][0]["content"]["parts"][-1]["text"]
```

---

## 4. Anthropic Claude API 상세 분석

Claude 모델을 쓰고 싶을 때 알아두어야 할 REST API 규격입니다.

### 핵심 파라미터 특징
1. **헤더(Headers) 규칙**:
   - `Authorization: Bearer ...` 대신 **`x-api-key: {API_KEY}`** 헤더를 씁니다.
   - **`anthropic-version: 2023-06-01`** 헤더를 필수로 함께 보내야 합니다.
2. **`max_tokens` 필수**:
   - OpenAI나 Gemini에서는 토큰 제한을 생략해도 기본값으로 동작하지만, Claude API에서는 **`max_tokens`를 생략하면 에러가 발생**합니다.
3. **`thinking` (확장/적응형 추론)과 `temperature` 제약**:
   - 최신 Claude 모델에서 `thinking`을 활성화(`{"type": "adaptive"}` 또는 `{"type": "enabled", "budget_tokens": 2048}`)하면 **`temperature`를 `1.0` 이외의 값(예: `0.3`)으로 바꿀 수 없습니다.** (바꾸면 `400 Bad Request` 발생)
   - 또한 `max_tokens` 안에 `thinking` 토큰이 포함되므로 `thinking`을 켤 때는 `max_tokens`를 넉넉하게 설정해야 합니다.

### Anthropic Claude 요청 JSON 예시
- **URL**: `POST https://api.anthropic.com/v1/messages`

```json
{
  "model": "claude-sonnet-4-5",
  "system": "당신은 숙련된 개발자입니다.",
  "messages": [
    {
      "role": "user",
      "content": "이 git diff를 요약해 주세요."
    }
  ],
  "max_tokens": 600,
  "temperature": 0.3
}
```

---

## 5. 우리 프로젝트(`example/ai_client.py`)에서의 적용 방식

우리 예제 코드의 [`ai_client.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/ai_client.py)는 위 3대 AI 서비스와 최신 파라미터 변화를 모두 자동으로 처리하도록 작성되어 있습니다.

```bash
# 1) OpenAI 표준 모델 사용 시 (max_completion_tokens + temperature 전송)
python3 example/main.py commit -model gpt-4o-mini -temperature 0.3

# 2) OpenAI 최신 GPT-5 / 추론 모델 사용 시 (자동으로 developer role + max_completion_tokens + reasoning_effort + verbosity 적용)
python3 example/main.py commit -model gpt-5.1

# 3) Google Gemini 모델 사용 시 (자동으로 generationConfig + maxOutputTokens 적용)
python3 example/main.py commit -model gemini-2.5-flash

# 4) Anthropic Claude 모델 사용 시 (자동으로 x-api-key 헤더 + system 분리 적용)
python3 example/main.py commit -model claude-sonnet-4-5
```

