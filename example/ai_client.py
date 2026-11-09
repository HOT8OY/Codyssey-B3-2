"""
[모듈 3: ai_client.py]
역할: 운영체제 환경변수에서 API Key를 안전하게 불러오고,
      REST API 방식으로 외부 AI 서버(OpenAI 또는 Google Gemini)에 요청을 보내 응답을 받아옵니다.
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
       - Body/Payload (실제로 보낼 프롬프트, 모델 이름, temperature, max_tokens 설정값)
    2. 파라미터 의미:
       - temperature: 낮을수록(0.0~0.3) 차분하고 정해진 양식대로 대답하고, 높을수록(0.8~1.0) 창의적으로 대답합니다.
       - max_tokens: AI가 한 번에 생성할 최대 글자(토큰) 분량을 제한해 과도한 비용을 막습니다.
    """
    api_key = get_api_key()

    # Google Gemini 키('AIza...'로 시작) 또는 모델명이 'gemini'로 시작하면 Gemini API 형식을 사용하고,
    # 그 외에는 OpenAI API 형식을 사용합니다.
    is_gemini = model.lower().startswith("gemini") or api_key.startswith("AIza")

    if is_gemini:
        effective_model = model if model.lower().startswith("gemini") else "gemini-2.0-flash"
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
    else:
        url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
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
        # 서버가 에러 상태 코드(401, 429 등)를 돌려준 경우 원인을 친절히 출력합니다.
        error_detail = e.read().decode("utf-8", errors="replace")
        if e.code == 401:
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
        # 인터넷이 끊겼거나 서버 주소에 연결할 수 없는 경우
        print(f"[ERROR] AI API 네트워크 연결 실패: {e.reason}")
        sys.exit(1)

    except json.JSONDecodeError:
        print("[ERROR] AI API 응답을 JSON으로 변환하는 데 실패했습니다.")
        sys.exit(1)

    # JSON 응답 상자 안에서 실제 AI가 작성한 글자만 꺼내어 반환합니다.
    try:
        if is_gemini:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        print(f"[ERROR] AI API 응답 구조가 예상과 다릅니다 ({e}): {data}")
        sys.exit(1)

