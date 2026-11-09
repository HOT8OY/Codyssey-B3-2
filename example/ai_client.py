"""
[모듈 3: ai_client.py]
역할: 운영체제 환경변수에서 API Key를 안전하게 불러오고,
      REST API 방식으로 외부 AI 서버(OpenAI, Google Gemini, Anthropic Claude)에
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


def is_openai_reasoning_or_gpt5_plus(model: str) -> bool:
    """
    OpenAI의 추론(Reasoning) 계열(o1, o3, o4 등)이나 최신 GPT-5 이상 모델인지 판별합니다.
    이 모델들은 구형 `max_tokens` 대신 `max_completion_tokens`를 요구하며,
    추론 모드 활성화 시 `temperature` 변경 제한이나 `developer` 역할(role)을 사용합니다.
    """
    m = model.lower()
    prefixes = ("gpt-5", "gpt-6", "o1", "o3", "o4")
    return any(m.startswith(p) for p in prefixes)


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
    2. 세대별 파라미터 차이 자동 대응:
       - OpenAI GPT-4o 계열: `max_tokens` 또는 `max_completion_tokens`, `temperature` 사용
       - OpenAI GPT-5+ / o-시리즈: `max_completion_tokens` 필수 사용, `developer` role 사용
       - Google Gemini 계열: `generationConfig` 내부에 `maxOutputTokens`, `temperature` 사용
       - Anthropic Claude 계열: `x-api-key` 헤더와 `max_tokens`, `system` 필드 분리 사용
    """
    api_key = get_api_key()
    model_lower = model.lower()

    # 1) 어떤 AI 서비스인지 모델명 또는 API Key 접두사로 자동 판별
    is_gemini = model_lower.startswith("gemini") or api_key.startswith("AIza")
    is_claude = model_lower.startswith("claude") or api_key.startswith("sk-ant-")

    if is_gemini:
        # [Google Gemini REST API]
        effective_model = model if model_lower.startswith("gemini") else "gemini-2.5-flash"
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
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
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

    elif is_claude:
        # [Anthropic Claude REST API]
        effective_model = model if model_lower.startswith("claude") else "claude-sonnet-4-5"
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": effective_model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

    else:
        # [OpenAI Chat Completions REST API]
        url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        if is_openai_reasoning_or_gpt5_plus(model):
            # GPT-5 / GPT-5.1+ / o-시리즈 최신 규격:
            # - system 대신 developer 역할 권장
            # - max_tokens 대신 max_completion_tokens 필수 (추론 토큰 + 출력 토큰 합산 예산)
            # - 추론 토큰이 예산을 다 쓰지 않도록 최소 여유분 보정 및 reasoning_effort="low" 설정
            safe_completion_tokens = max(max_tokens, 1500)
            payload = {
                "model": model,
                "messages": [
                    {"role": "developer", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_completion_tokens": safe_completion_tokens,
                "reasoning_effort": "low",
            }
            # GPT-5 계열은 verbosity 옵션("low", "medium", "high") 지원
            if model_lower.startswith(("gpt-5", "gpt-6")):
                payload["verbosity"] = "medium"
        else:
            # GPT-4o / GPT-4o-mini 등 표준 모델 규격:
            # max_completion_tokens는 최신 OpenAI API에서 max_tokens를 대체하는 표준 파라미터입니다.
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_completion_tokens": max_tokens,
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
            reason = "권한 거부 (해당 모델 접근 권한을 확인하세요)"
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
            # Gemini는 thinking이 켜져 있을 때 parts가 여러 개(thought 파트 + 최종 text 파트)일 수 있으므로
            # 마지막 텍스트 파트를 가져옵니다.
            parts = data["candidates"][0]["content"]["parts"]
            text_parts = [p["text"] for p in parts if "text" in p and not p.get("thought", False)]
            return (text_parts[-1] if text_parts else parts[-1]["text"]).strip()
        elif is_claude:
            # Claude 역시 thinking 블록과 text 블록이 함께 올 수 있으므로 type == "text"인 블록을 추출합니다.
            content_blocks = data["content"]
            text_blocks = [b["text"] for b in content_blocks if b.get("type") == "text"]
            return text_blocks[-1].strip()
        else:
            return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        print(f"[ERROR] AI API 응답 구조가 예상과 다릅니다 ({e}): {data}")
        sys.exit(1)
