# 최신 AI REST API 사용법 및 모델별 지원/미지원 파라미터 완벽 가이드

이 문서는 **최근 1년 이내 출시된 최신 AI 모델들** — **OpenAI (GPT-6 / 6.1 계열)**, **Google (Gemini 4 / 3.8 / 3.1 계열)**, **Anthropic (Claude 5 / 4.6+ 계열)** — 의 REST API 호출 구조와 **패러다임 전환으로 인해 사라지거나 금지된(400 에러 유발) 옵션들, 그리고 모델별로 허용되는 옵션의 정확한 경계**를 정리한 레퍼런스입니다.

---

## 1. 왜 최근 1년 사이 3대 AI의 기존 옵션들이 대거 금지되었을까?

과거(GPT-4, Gemini 1.5, Claude 3 시절)의 AI가 단순 **'다음 단어 확률 예측기'**였다면, 최근 1년 내 출시된 모든 주력 모델은 답변을 내놓기 전 내부적으로 수백~수천 토큰의 **사고 과정(Chain-of-Thought, CoT)**을 거치는 **'추론(Reasoning) 모델'**로 통합되었습니다.

이 때문에 3사 공통으로 다음 변화가 일어났습니다:
1. **확률 흔들기(`temperature`, `top_p`, `top_k`)의 종말**: 추론 도중 확률 분포를 인위적으로 흔들면 논리 체인이 붕괴되므로, 3사 모두 샘플링 파라미터를 **전면 제거하거나 전송 시 `400 Bad Request` 에러**를 반환합니다.
2. **토큰 숫자 예산(Budget) $\rightarrow$ 단계형 강도(Effort / Level)로 전환**: 개발자가 생각할 토큰 수를 숫자로 직접 지정하던 방식(`thinkingBudget`, `budget_tokens`)이 폐지되고, `"low"`, `"medium"`, `"high"` 같은 **추론 강도 옵션**으로 통일되었습니다.
3. **고성능 모델의 '추론 끄기(`none` / `minimal`)' 불가**: 상위 플래그십 모델들은 추론 과정 자체가 모델 지능의 핵심이므로 아예 추론을 끄는 옵션을 허용하지 않습니다.

---

## 2. 한눈에 보는 3대 AI 최신 스펙 및 금지 옵션 요약표

| 구분 | OpenAI (GPT-6 / 6.1 계열) | Google (Gemini 4 / 3.8 / 3.1 계열) | Anthropic (Claude 5 / 4.6+ 계열) |
| :--- | :--- | :--- | :--- |
| **API Key 시작 형태** | `sk-...` 또는 `sk-proj-...` | **`AQ.Ab...`** (`AQ.` 시작 Auth Key) | `sk-ant-...` |
| **최신 주력 모델 ID** | `gpt-6-astra`, `gpt-6.1-sol`,<br>`gpt-6.1-terra`, `gpt-6-luna` | `gemini-4-carbon`, `gemini-4-argon`,<br>`gemini-3.8-flash`, `gemini-3.1-pro` | `claude-opus-5`, `claude-sonnet-5`<br>*(API 버전: `2026-10-21`)* |
| **시스템 지시문 위치** | `messages` 내 **`role: "developer"`**<br>*(구형 `"system"` 대체)* | 최상위 `systemInstruction` 필드 | 최상위 `system` 필드 |
| **최대 토큰 제한 옵션** | **`max_completion_tokens`**<br>*(구형 `max_tokens` 전송 시 400 에러)* | `generationConfig.maxOutputTokens` | `max_tokens` *(필수 입력)* |
| **추론(CoT) 제어 옵션** | **`reasoning_effort`**<br>(`"none"`, `"low"`, `"medium"`, `"high"`, `"xhigh"`, `"max"`) | **`generationConfig.thinkingConfig.thinkingLevel`**<br>(`"minimal"`, `"low"`, `"medium"`, `"high"`) | **`thinking: {"type": "adaptive"}`** +<br>**`output_config: {"effort": "..."}`** |
| **답변 길이/상세도 제어** | **`verbosity`** (`"low"`, `"medium"`, `"high"`) | 프롬프트 지시문으로 제어 | 프롬프트 지시문으로 제어 |
| **전송 시 400 에러가 나는<br>대표 금지(폐지) 옵션** | - `max_tokens`<br>- 추론 활성 시: `temperature`, `top_p`, `presence_penalty`, `frequency_penalty`, `logprobs`<br>- Astra/Sol에서 `reasoning_effort: "none"` | - `thinkingBudget` *(구형 숫자 예산)*<br>- `temperature`, `topP`, `topK`, 페널티 옵션<br>- Argon/3.8-Flash에서 `thinkingLevel: "minimal"` | - `temperature`, `top_p`, `top_k` *(기본값 `1.0`조차 전송 금지)*<br>- Assistant Prefill *(답변 첫머리 미리 채우기)*<br>- `thinking.budget_tokens` *(수동 토큰 예산)* |

---

## 3. OpenAI (GPT-6 / 6.1 시리즈) 모델별 가능·불가능 옵션 상세

OpenAI의 GPT-6 제품군은 **Astra, Sol, Terra, Luna** 4가지 티어로 나뉘며, **어떤 모델을 쓰느냐, 그리고 `reasoning_effort`를 무엇으로 두느냐**에 따라 허용되는 파라미터가 엄격히 갈립니다.

### ① 모델별 지원 옵션 매트릭스

| 모델 ID | 티어 및 특징 | 허용되는 `reasoning_effort` | 추론 끄기 (`"none"` / `"minimal"`) | `temperature`, `top_p` 사용 가능 여부 | `verbosity` 지원 |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **`gpt-6-astra`** | 플래그십 최고 지능 | `"low"`, `"medium"`, `"high"`, `"xhigh"`, `"max"` | ❌ **불가능 (400 에러)** | ❌ **절대 불가** (추론을 끌 수 없으므로 항상 400 에러) | ✅ (`low`/`medium`/`high`) |
| **`gpt-6.1-sol`** | 코딩·복합 추론 주력 | `"low"`, `"medium"`(기본), `"high"`, `"xhigh"`, `"max"` | ❌ **불가능 (400 에러)** | ❌ **절대 불가** (추론을 끌 수 없으므로 항상 400 에러) | ✅ (`low`/`medium`/`high`) |
| **`gpt-6.1-terra`** | 시각 추론·컴퓨터 제어·작문 | `"none"`, `"low"`, `"medium"`, `"high"`, `"xhigh"`, `"max"` | ✅ 가능 | ⚠️ **조건부 가능** (`reasoning_effort: "none"`을 명시했을 때만 허용, 기본값일 땐 400 에러) | ✅ (`low`/`medium`/`high`) |
| **`gpt-6-luna`** | 초고속·초저비용 경량 | `"none"` ~ `"max"` 전 범위 | ✅ 가능 | ⚠️ **조건부 가능** (`reasoning_effort: "none"`을 명시했을 때만 허용, 기본값일 땐 400 에러) | ✅ (`low`/`medium`/`high`) |

### ② OpenAI 호출 시 자주 겪는 `400 Bad Request` 함정 4가지
1. **`max_tokens` 사용 금지**: 구형 `max_tokens`를 보내면 즉시 `Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.` 에러가 발생합니다.
2. **추론 활성 상태에서 5대 샘플링 파라미터 금지**:
   - `reasoning_effort`를 생략(기본값 `"medium"` 적용)하거나 `"low"` 이상으로 둔 상태에서는 **`temperature`, `top_p`, `presence_penalty`, `frequency_penalty`, `logprobs`** 중 단 하나라도 JSON에 포함되면 400 에러가 납니다.
3. **Astra와 6.1 Sol에서 `"none"` 설정 금지**:
   - `gpt-6-astra`와 `gpt-6.1-sol`은 무조건 생각을 거쳐야 하는 모델입니다. 속도를 높이겠다고 `reasoning_effort: "none"`이나 `"minimal"`을 넣으면 400 에러가 납니다. **4개 모델 모두에서 에러 없이 도는 최소 추론 단계는 `"low"`입니다.**
4. **Function/Tool Calling 시 주의점**:
   - 복잡한 도구 호출과 높은 추론 강도를 함께 쓸 때는 구형 `/v1/chat/completions` 대신 신규 **`/v1/responses`** 엔드포인트(토큰 제한 파라미터명: `max_output_tokens`)를 쓰는 것이 권장됩니다.

### ③ 모든 GPT-6 모델에서 100% 안전하게 동작하는 표준 JSON 예시
```json
{
  "model": "gpt-6.1-sol",
  "messages": [
    {
      "role": "developer",
      "content": "당신은 숙련된 소프트웨어 엔지니어입니다. 주어진 git diff를 바탕으로 커밋 메시지를 작성하세요."
    },
    {
      "role": "user",
      "content": "[변경 파일]\n- main.py\n\n[Git Diff]\n+ print('hello')"
    }
  ],
  "reasoning_effort": "low",
  "verbosity": "medium",
  "max_completion_tokens": 1500
}
```

---

## 4. Google Gemini (Gemini 4 / 3.8 / 3.1 시리즈) 모델별 가능·불가능 옵션 상세

Google 역시 최신 모델에서 숫자 예산(`thinkingBudget`)과 샘플링 옵션(`temperature` 등)을 폐기하고 **`thinkingLevel`** 체계로 전환했습니다.

### ① 모델별 지원 옵션 매트릭스

| 모델 ID | 티어 및 특징 | 허용되는 `thinkingLevel` | `"minimal"` 단계 지원 여부 | 구형 `thinkingBudget` (숫자) | `temperature` / `topP` / `topK` |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **`gemini-4-carbon`** | 프론티어 (장기 엔지니어링·보안) | `"low"`, `"medium"`, `"high"` | ❌ **불가능 (400 에러)** | ❌ **금지 (400 에러)** | ❌ 지원 중단 (무시되거나 페널티 결합 시 400 에러) |
| **`gemini-4-argon`** | 플래그십 추론 (고급 코딩·수학) | `"low"`, `"medium"`(기본), `"high"` | ❌ **불가능 (400 에러)** | ❌ **금지 (400 에러)** | ❌ 지원 중단 |
| **`gemini-3.8-flash`** | 초고속·고효율 주력 모델 | `"low"`, `"medium"`(기본), `"high"` | ❌ **불가능 (400 에러)** | ❌ **금지 (400 에러)** | ❌ 지원 중단 |
| **`gemini-3.1-pro`** | 범용 고성능 문서·추론 모델 | `"minimal"`, `"low"`, `"medium"`, `"high"` | ✅ 가능 | ❌ **금지 (400 에러)** | ❌ 지원 중단 |

### ② Gemini 호출 시 자주 겪는 `400 Bad Request` 함정 3가지
1. **구형 `thinkingBudget` 사용 또는 혼용 금지**:
   - Gemini 2.5 시절처럼 `"thinkingBudget": 0`이나 `"thinkingBudget": 1024`를 보내면 `"Thinking budget is not supported for this model. Use thinking level instead."`라는 400 에러가 발생합니다.
2. **`gemini-4-argon` 및 `gemini-3.8-flash`에서 `thinkingLevel: "minimal"` 금지**:
   - 문서상 enum 목록에는 `"minimal"`이 존재하지만, **`gemini-4-argon`과 `gemini-3.8-flash`는 `"minimal"`을 지원하지 않아 `400 INVALID_ARGUMENT` 에러**를 냅니다.
   - 따라서 전 모델 공통으로 빠른 응답을 원할 때는 반드시 **`"thinkingLevel": "low"`**를 사용해야 합니다!
3. **`AQ.Ab...` 인증 키(Auth Key) 규격**:
   - 최신 Google AI Studio / Vertex AI 키는 과거의 `AIza...`가 아니라 **`AQ.Ab...`**로 시작합니다. 키 형식을 검사하는 코드가 있다면 반드시 `AQ.` 접두사를 허용해야 합니다.

### ③ 모든 최신 Gemini 모델에서 안전하게 동작하는 표준 JSON 예시
- **URL**: `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-4-argon:generateContent?key=AQ.Ab...`

```json
{
  "systemInstruction": {
    "parts": [
      { "text": "당신은 숙련된 소프트웨어 엔지니어입니다." }
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
    "maxOutputTokens": 1500,
    "thinkingConfig": {
      "thinkingLevel": "low"
    }
  }
}
```

---

## 5. Anthropic Claude (Claude 5 / 4.6~4.8 시리즈, API `2026-10-21`) 가능·불가능 옵션 상세

Anthropic은 Claude 4.6 ~ 5 세대와 새 API 버전(`2026-10-21`)을 발표하면서 가장 과감하게 레거시 기능들을 제거했습니다.

### ① 지원 / 미지원(Breaking Changes) 핵심 정리

| 기능 / 파라미터 | 과거 방식 (폐지 / 400 에러) | 최신 방식 (Claude 4.6 ~ 5+ 표준) | 주의사항 설명 |
| :--- | :--- | :--- | :--- |
| **샘플링 파라미터** | `temperature`, `top_p`, `top_k` | **완전 삭제 (생략 필수)** | `2026-10-21` 버전에서는 기본값인 `temperature: 1.0`조차 보내면 **`400 Bad Request`** 발생! 아예 키 자체를 빼야 합니다. |
| **추론(Thinking) 활성화** | `thinking: {"type": "enabled", "budget_tokens": 4000}` | **`thinking: {"type": "adaptive"}`** | 수동으로 `budget_tokens` 숫자를 넣으면 `400 ValidationException` 발생. 모델이 난이도에 따라 스스로 추론 여부를 결정합니다. |
| **추론 강도 조절** | `budget_tokens` 숫자로 조절 | **`output_config: {"effort": "low"}`** | `"low"`, `"medium"`, `"high"`, `"xhigh"`, `"max"` 단계로 추론 깊이를 제어합니다. |
| **출력 형식 강제** | **Assistant Prefill**<br>(`messages` 끝에 `role: "assistant"` 미리 넣기) | **전면 금지 (400 에러)** $\rightarrow$<br>`output_config.format` 또는 프롬프트 사용 | 답변 첫머리를 강제하던 Prefill 기법은 최신 Claude에서 즉시 400 에러를 반환합니다. |
| **인증 헤더** | `x-api-key: sk-ant-...` | `Authorization: Bearer sk-ant-...`<br>*(또는 `x-api-key` 호환)* | 최신 SDK(Python v2.0.0+)는 `2026-10-21` 버전과 `Bearer` 헤더를 기본으로 사용합니다. |

### ② 최신 Claude 5 표준 JSON 예시 (`POST https://api.anthropic.com/v1/messages`)
```json
{
  "model": "claude-sonnet-5",
  "system": "당신은 숙련된 소프트웨어 엔지니어입니다.",
  "messages": [
    {
      "role": "user",
      "content": "이 git diff를 요약해 주세요."
    }
  ],
  "max_tokens": 1500,
  "thinking": {
    "type": "adaptive"
  },
  "output_config": {
    "effort": "low"
  }
}
```

---

## 6. 결론: 3대 AI를 모두 호환하는 가장 안전한 황금 규칙

최근 1년 이내의 최신 모델들을 호출할 때 `400 Bad Request` 에러를 피하는 핵심 원칙 4가지입니다:

1. **`temperature`, `top_p`, `top_k`는 JSON Payload에 넣지 않는다.** (미션 요구사항 때문에 CLI 옵션 `-temperature`를 받더라도, 최신 모델 API로 전송할 때는 빼는 것이 에러를 막는 길입니다.)
2. **추론 강도는 3사 모두 공통으로 지원되는 `"low"`를 기본으로 쓴다.**
   - OpenAI: `"reasoning_effort": "low"` (`"none"`은 Astra/Sol에서 에러)
   - Gemini: `"thinkingConfig": {"thinkingLevel": "low"}` (`"minimal"`은 Argon/Flash에서 에러)
   - Claude: `"thinking": {"type": "adaptive"}`, `"output_config": {"effort": "low"}`
3. **최대 토큰 수는 추론 토큰이 합산되므로 최소 `1500` 이상으로 설정한다.**
   - OpenAI는 반드시 `max_completion_tokens` 이름을 사용한다.
4. **시스템 프롬프트는 각 사의 최신 전용 위치에 넣는다.**
   - OpenAI: `"role": "developer"`, Gemini: `"systemInstruction"`, Claude: `"system"`
