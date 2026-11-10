# 최신 AI REST API 사용법 및 모델·파라미터 완벽 가이드

이 문서는 **OpenAI (GPT-6 / 6.1 계열)**, **Google (Gemini 4 / 3.8 계열)**, **Anthropic (Claude 5 계열)** 3대 AI 서비스의 최신 모델 분류 체계, API Key 규격, 그리고 REST API 호출 파라미터를 공식 스펙 기반으로 정리한 레퍼런스입니다. *(구형 GPT-4 이하 레거시 규격은 제외하고 최신 표준만 다룹니다.)*

---

## 1. 한눈에 보는 3대 AI REST API 비교표

| 구분 | OpenAI (GPT-6 / 6.1 계열) | Google (Gemini 4 / 3.8 계열) | Anthropic (Claude 5 계열) |
| :--- | :--- | :--- | :--- |
| **API Key 시작 형태** | `sk-...` 또는 `sk-proj-...` | **`AQ.Ab...`** (`AQ.` 시작 Auth Key)<br>*(구형: `AIza...`)* | `sk-ant-...` |
| **모델 라인업 분류** | **Astra / Sol / Terra / Luna**<br>(`gpt-6-astra`, `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-luna`) | **Carbon / Argon / Flash / Pro**<br>(`gemini-4-carbon`, `gemini-4-argon`, `gemini-3.8-flash`, `gemini-3.1-pro`) | **Opus / Sonnet / Haiku**<br>(`claude-opus-5`, `claude-sonnet-5`) |
| **REST 엔드포인트 (URL)** | `https://api.openai.com/v1/chat/completions`<br>*(또는 `/v1/responses`)* | `https://generativelanguage.googleapis.com/v1beta/models/{모델명}:generateContent?key={API_KEY}` | `https://api.anthropic.com/v1/messages` |
| **인증 방식 (Header/Query)** | `Authorization: Bearer {API_KEY}` | URL 쿼리(`?key=AQ.Ab...`) 또는<br>`x-goog-api-key: {API_KEY}` | `x-api-key: {API_KEY}`<br>`anthropic-version: 2023-06-01` |
| **시스템 지시문 위치** | `messages` 배열 내<br>**`role: "developer"`** | 최상위 `systemInstruction` 필드 | 최상위 `system` 필드 |
| **최대 토큰 제한 파라미터** | **`max_completion_tokens`**<br>*(Responses API는 `max_output_tokens`)* | `generationConfig.maxOutputTokens` | `max_tokens` *(필수 입력)* |
| **추론(생각) 깊이 조절** | **`reasoning_effort`**<br>(`"none"`, `"low"`, `"medium"`, `"high"`, `"xhigh"`, `"max"`) | **`generationConfig.thinkingConfig.thinkingLevel`**<br>(`"minimal"`, `"low"`, `"medium"`, `"high"`) | **`thinking`**<br>(`type: "adaptive"` 또는 `"enabled"`) |
| **답변 길이/상세도 스타일** | **`verbosity`**<br>(`"low"`, `"medium"`, `"high"`) | 프롬프트 지시문으로 제어 | 프롬프트 지시문으로 제어 |

---

## 2. OpenAI API (GPT-6 / 6.1 시리즈: Astra, Sol, Terra, Luna)

OpenAI의 최신 GPT-6 / 6.1 제품군은 작업의 난이도, 속도, 비용 효율성에 따라 **Astra, Sol, Terra, Luna** 4가지 티어로 분류되며, 모두 **105만(1.05M) 토큰 컨텍스트 윈도우**와 **최대 12만 8천(128K) 출력 토큰**을 지원합니다.

### ① GPT-6 / 6.1 모델 라인업 비교

| 모델 ID | 분류 (티어) | 입력 / 출력 가격<br>*(1M 토큰 기준)* | 지원하는 `reasoning_effort` | 핵심 특징 및 추천 용도 |
| :--- | :--- | :---: | :--- | :--- |
| **`gpt-6-astra`** | **Astra** (플래그십) | \$10 / \$50 | `low`, `medium`, `high`, `xhigh`, `max`<br>*(none/minimal 불가)* | 최고 지능과 최고 수준의 추론 능력. 가장 복잡한 아키텍처 설계 및 심층 다단계 추론 작업용 |
| **`gpt-6.1-sol`** | **Sol** (균형형 고성능) | \$2 / \$10 | `low`, `medium`(기본), `high`, `xhigh`, `max`<br>*(none/minimal 불가)* | Astra에 근접한 코딩·복합 추론 성능을 합리적인 비용으로 제공하는 주력 개발 모델 |
| **`gpt-6.1-terra`** | **Terra** (에이전트/작문) | \$1 / \$5 | `low` ~ `max` | 시각적 추론(Visual Reasoning), 컴퓨터 제어(Computer Use), 명확하고 자연스러운 문서/커뮤니케이션 작성 특화 |
| **`gpt-6-luna`** | **Luna** (초고속/경량) | \$0.10 / \$0.50 | `none` ~ `max` 전 범위 허용 | 속도가 가장 빠르고 비용이 극대화된 경량 모델. 커밋/PR 초안 생성 같은 일상적 개발 자동화에 최적 |

### ② 핵심 파라미터 설명

1. **`max_completion_tokens` (구형 `max_tokens` 대체)**
   - 모델이 **내부적으로 생각하는 추론 토큰(Reasoning Tokens)**과 **화면에 출력되는 최종 답변 토큰**을 합산한 최대 토큰 한도입니다.
   - 주의: 이 값을 너무 작게(예: `200`) 설정하면 내부 추론 과정에서 토큰을 모두 소모해 정작 화면에 보이는 답변이 잘릴 수 있으므로 `1500` 이상으로 여유 있게 주거나 `reasoning_effort`를 `"low"`로 낮추는 것이 좋습니다.
2. **`reasoning_effort` (추론 강도 조절)**
   - 모델이 답변하기 전에 얼마나 깊이 생각할지 지정합니다.
   - `gpt-6-astra`와 `gpt-6.1-sol`은 최소 `"low"`부터 지원하므로, 모든 GPT-6 모델에서 공통으로 호환되게 하려면 **`"low"`** 또는 **`"medium"`**을 사용하는 것이 안전합니다.
3. **`verbosity` (답변 상세도 조절)**
   - `"low"`(핵심만 간결하게), `"medium"`(표준 상세도, 기본값), `"high"`(배경 설명과 예시까지 풍부하게) 중 하나로 출력 문장 스타일을 제어합니다.
4. **`role: "developer"` 및 `temperature` 주의점**
   - 시스템 지시문은 `"role": "developer"`로 전달합니다.
   - 추론(`reasoning_effort`)이 동작할 때는 기존 샘플링 파라미터인 `temperature`를 임의 값으로 바꾸면 `400 Bad Request`가 발생할 수 있으므로 생략하는 것이 표준입니다.

### ③ OpenAI 요청 JSON 예시 (`POST https://api.openai.com/v1/chat/completions`)
```json
{
  "model": "gpt-6-luna",
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

## 3. Google Gemini API (Gemini 4 / 3.8 / 3.1 시리즈: Carbon, Argon, Flash, Pro)

### ① API Key 규격 변화 (`AQ.Ab...`)
- 과거 Google API 키는 `AIza...`로 시작했으나, 최신 Google AI Studio 및 Vertex AI 환경에서 발급되는 인증 키(Auth Key)는 서비스 자격 증명 및 보안 강화를 위해 **`AQ.Ab...` (`AQ.` 접두사)** 형태로 시작합니다.
- 공식 Gemini REST 엔드포인트(`generativelanguage.googleapis.com`)에 `?key=AQ.Ab...` 형태로 그대로 전달하면 정상 인증됩니다.

### ② Gemini 공식 모델 라인업 비교 (`gemini-4-carbon`, `gemini-4-argon`, `gemini-3.8-flash`, `gemini-3.1-pro`)
Google은 Gemini 4 세대부터 원소 기호 기반 코드명(**Carbon**, **Argon**)을 도입했으며, 초고속 경량 라인은 **Gemini 3.8 Flash**, 기존 Pro 라인은 **Gemini 3.1 Pro**로 구성되어 있습니다.

| 모델 ID | 분류 (티어) | 핵심 특징 및 추천 용도 |
| :--- | :--- | :--- |
| **`gemini-4-carbon`** | **Carbon** (Gemini 4 프론티어) | 장기(Long-horizon) 소프트웨어 엔지니어링, 복잡한 다단계 실행, 사이버보안(취약점 분석 및 패치 검증)에 특화된 최상위 모델 |
| **`gemini-4-argon`** | **Argon** (Gemini 4 플래그십) | 고급 코딩, 복잡한 수학·과학 문제 해결, 멀티스텝 에이전트 워크플로우용 주력 추론 모델 (1M 통합 컨텍스트 윈도우 지원) |
| **`gemini-3.8-flash`** | **Flash** (Gemini 3.8 초고속/고효율) | 빠른 응답 속도와 뛰어난 가성비를 갖춘 고지능 주력(Workhorse) 모델. 커밋 메시지 및 PR 초안 자동 생성에 가장 적합 |
| **`gemini-3.1-pro`** | **Pro** (Gemini 3.1 고성능) | 방대한 문서 분석, 복합 추론, 지식 검색 등 기존 Pro 포지션을 담당하는 모델 |

### ③ 핵심 파라미터 (`generationConfig` & `thinkingLevel`)

1. **`systemInstruction`**: 시스템 프롬프트를 넣는 최상위 필드입니다.
2. **`generationConfig.maxOutputTokens`**: 최대 출력 토큰 수를 지정합니다.
3. **`generationConfig.thinkingConfig.thinkingLevel`**:
   - 최신 Gemini 모델(`gemini-4-argon`, `gemini-3.8-flash` 등)은 복잡한 토큰 숫자 예산 대신 단계별 추론 설정인 **`thinkingLevel`**을 사용합니다.
   - 허용 값: `"minimal"` (최소 지연 시간), `"low"` (가벼운 추론), `"medium"` (기본값, 균형), `"high"` (최대 깊이 추론)

### ④ Google Gemini 요청 JSON 예시
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
    "temperature": 0.3,
    "maxOutputTokens": 1500,
    "thinkingConfig": {
      "thinkingLevel": "low"
    }
  }
}
```

---

## 4. Anthropic Claude API (`POST https://api.anthropic.com/v1/messages`)

- **헤더**: `x-api-key: sk-ant-...` 및 `anthropic-version: 2023-06-01` 필수
- **필수 파라미터**: `max_tokens`를 반드시 명시해야 하며, 적응형 추론(`"thinking": {"type": "adaptive"}`) 활성화 시에는 `temperature`를 변경하지 않고 생략합니다.

```json
{
  "model": "claude-sonnet-5",
  "system": "당신은 숙련된 소프트웨어 엔지니어입니다.",
  "messages": [
    { "role": "user", "content": "이 git diff를 요약해 주세요." }
  ],
  "max_tokens": 1500,
  "temperature": 0.3
}
```

---

## 5. 우리 프로젝트([`example/ai_client.py`](file:///Users/4321qwaszx9029/Codyssey-B3-2/example/ai_client.py))에서의 실행 예시

우리 예제 코드는 `AI_API_KEY`가 `AQ.Ab...`로 시작하면 자동으로 Gemini REST API로, `sk-...`로 시작하면 OpenAI REST API로 연결하며 모델별 최신 파라미터를 자동 구성합니다.

```bash
# 1) OpenAI GPT-6 모델들로 실행할 때
export AI_API_KEY="sk-proj-..."
python3 example/main.py commit -model gpt-6-luna
python3 example/main.py pr -model gpt-6.1-sol
python3 example/main.py pr -model gpt-6.1-terra
python3 example/main.py pr -model gpt-6-astra

# 2) Google Gemini 모델들로 실행할 때
export AI_API_KEY="AQ.Ab..."
python3 example/main.py commit -model gemini-3.8-flash
python3 example/main.py pr -model gemini-3.1-pro
python3 example/main.py pr -model gemini-4-argon
python3 example/main.py pr -model gemini-4-carbon
```
