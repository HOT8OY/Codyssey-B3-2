"""
[모듈 3: ai_client.py]
역할: 운영체제 환경변수에서 API Key를 안전하게 불러오고,
      REST API 방식으로 외부 AI 서버(OpenAI GPT-6 계열, Google Gemini 4/3.8 계열, Anthropic Claude)에
      요청을 보내 응답을 받아옵니다.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def get_api_key() -> str:
    """
    환경변수 `AI_API_KEY`에서 API 키를 읽어옵니다.
    보안을 위해 코드 안에 API 키를 직접 적지(하드코딩하지) 않습니다.
    """
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.")
        print('## 예) export AI_API_KEY="YOUR_KEY"')
        sys.exit(1)
    return api_key


def is_gemini_request(model: str, api_key: str) -> bool:
    """
    모델명이나 API Key 접두사를 보고 Google Gemini API 요청인지 판별합니다.
    - 최신 Google AI Studio / Vertex AI 인증 키는 'AQ.Ab...'('AQ.')로 시작합니다. (구형 키는 'AIza...')
    - 최신 Gemini 모델명은 'gemini-4-argon', 'gemini-4-carbon', 'gemini-3.8-flash' 등입니다.
    """
    m = model.lower()
    is_gemini_model = m.startswith("gemini") or any(
        tier in m for tier in ("argon", "carbon", "flash")
    )
    is_gemini_key = api_key.startswith("AQ.") or api_key.startswith("AIza")
    return is_gemini_model or is_gemini_key


def call_ai_api(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """
    AI 서버에 HTTP POST 요청을 1회 보내고, AI가 작성한 답변 텍스트를 반환합니다.

    [초심자 학습 포인트]
    1. REST API의 3요소:
       - URL (어느 서버 주소로 보낼지)
       - Headers (내가 누구인지 증명하는 API 키, 데이터 형식은 JSON이라는 표시)
       - Body/Payload (실제로 보낼 프롬프트, 모델 이름, 토큰 제한 등 설정값)
    2. 최신 모델 라인업 및 파라미터 규격 (GPT-4 이하 레거시 제외):
       - OpenAI GPT-6 계열 (`gpt-6-astra`, `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-luna`):
         * `role: "developer"` 사용
         * `max_completion_tokens` 사용 (추론 토큰 + 출력 토큰 통합 한도)
         * `reasoning_effort` ("low", "medium", "high", "xhigh", "max") 및 `verbosity` ("low", "medium", "high") 지원
       - Google Gemini 계열 (`gemini-4-carbon`, `gemini-4-argon`, `gemini-3.8-flash`, `gemini-3.1-pro`):
         * API Key가 `AQ.Ab...`로 시작
         * `generationConfig` 내 `maxOutputTokens`, `thinkingConfig.thinkingLevel` ("low", "medium", "high") 사용
       - Anthropic Claude 계열 (`claude-opus-5`, `claude-sonnet-5`, 최신 `2026-10-21` 규격):
         * `thinking: {"type": "adaptive"}` 및 `output_config: {"effort": "low"}` 사용
    """
    api_key = get_api_key()
    model_lower = model.lower()

    # 1) 어떤 AI 서비스인지 모델명 또는 API Key 접두사로 자동 판별
    is_gemini = is_gemini_request(model, api_key)
    is_claude = model_lower.startswith("claude") or api_key.startswith("sk-ant-")

    # 내부 추론(Thinking/Reasoning) 토큰과 최종 출력 토큰이 합산되므로 3사 공통으로 최소 1500 토큰 확보
    safe_tokens = max(max_tokens, 1500)

    # 참고: 최근 1년 내 출시된 최신 추론 모델들(GPT-6, Gemini 4/3.8, Claude 5/2026-10-21)은
    # 샘플링 파라미터(temperature 등)를 지원하지 않거나 전송 시 400 에러를 반환합니다.
    # 따라서 CLI 요구사항으로 받은 temperature 인자는 하위 호환 시그니처로만 유지하고,
    # 실제 요청 Payload에서는 추론 강도("low") 옵션으로 제어합니다.
    _ = temperature

    if is_gemini:
        # [Google Gemini REST API (gemini-4-carbon / gemini-4-argon / gemini-3.8-flash / gemini-3.1-pro)]
        # 사용자가 기본값(gpt-6-luna)을 그대로 둔 채 Gemini 키(AQ.Ab...)를 넣은 경우 자동으로 gemini-3.8-flash로 전환
        effective_model = model if model_lower.startswith("gemini") else "gemini-3.8-flash"
        gemini_base = os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com")
        url = (
            f"{gemini_base}/v1beta/models/"
            f"{effective_model}:generateContent?key={api_key}"
        )
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            "generationConfig": {
                "maxOutputTokens": safe_tokens,
                "thinkingConfig": {
                    # Argon과 3.8-Flash는 "minimal" 미지원(400 에러)이므로 전 모델 공통 호환되는 "low" 사용
                    "thinkingLevel": "low"
                },
            },
        }

    elif is_claude:
        # [Anthropic Claude REST API (claude-opus-5 / claude-sonnet-5, 최신 2026-10-21 규격)]
        effective_model = model if model_lower.startswith("claude") else "claude-sonnet-5"
        url = os.getenv("CLAUDE_API_URL", "https://api.anthropic.com/v1/messages")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2026-10-21",
        }
        payload = {
            "model": effective_model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": safe_tokens,
            "thinking": {
                "type": "adaptive"
            },
            "output_config": {
                "effort": "low"
            },
        }

    else:
        # [OpenAI Chat Completions REST API (GPT-6 Astra / Sol / Terra / Luna)]
        url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # Astra와 6.1 Sol은 reasoning_effort="none" 미지원(400 에러)이므로 전 모델 공통 호환되는 "low" 사용
        payload = {
            "model": model,
            "messages": [
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_completion_tokens": safe_tokens,
            "reasoning_effort": "low",
            "verbosity": "medium",
        }

    # 파이썬 딕셔너리(payload) -> JSON 문자열 -> 네트워크 전송용 바이트(utf-8)로 변환
    request_body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=request_body, headers=headers, method="POST")

    try:
        # 서버에 요청을 보내고 응답을 기다립니다 (최대 30초 대기)
        with urllib.request.urlopen(req, timeout=30) as response:
            response_text = response.read().decode("utf-8")
            data = json.loads(response_text)

    except urllib.error.HTTPError as e:
        error_detail = e.read().decode("utf-8", errors="replace")
        if e.code == 400:
            reason = "잘못된 요청 파라미터 (모델 이름이나 지원하지 않는 옵션인지 확인하세요)"
        elif e.code == 401:
            reason = "인증 실패 (API Key가 올바르지 않습니다)"
        elif e.code == 403:
            reason = "권한 거부 (해당 모델 접근 권한 또는 API 활성화 여부를 확인하세요)"
        elif e.code == 429:
            reason = "요청 한도 초과 (짧은 시간 내 너무 많이 호출했거나 잔여 크레딧이 부족합니다)"
        else:
            reason = f"HTTP {e.code} 오류"
        print(f"[ERROR] AI API 호출 실패 - {reason}\n상세 응답: {error_detail}")
        sys.exit(1)

    except urllib.error.URLError as e:
        print(f"[ERROR] AI API 네트워크 연결 실패: {e.reason}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("[ERROR] AI API 응답을 JSON으로 변환하는 데 실패했습니다.")
        sys.exit(1)

    # JSON 응답 상자 안에서 실제 AI가 작성한 글자만 꺼내어 반환합니다.
    try:
        if is_gemini:
            parts = data["candidates"][0]["content"]["parts"]
            text_parts = [p["text"] for p in parts if "text" in p and not p.get("thought", False)]
            return (text_parts[-1] if text_parts else parts[-1]["text"]).strip()
        elif is_claude:
            content_blocks = data["content"]
            text_blocks = [b["text"] for b in content_blocks if b.get("type") == "text"]
            return text_blocks[-1].strip()
        else:
            return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        print(f"[ERROR] AI API 응답 구조가 예상과 다릅니다 ({e}): {data}")
        sys.exit(1)
