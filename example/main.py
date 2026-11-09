#!/usr/bin/env python3
"""
[모듈 5 (메인 실행 파일): main.py]
역할: 사용자가 터미널에 입력한 명령어(commit / pr)와 옵션(-model, -temperature, -max-tokens, -safe-mode)을
      읽어 들이고, 나머지 4개 모듈을 순서대로 호출해 최종 결과를 화면에 출력합니다.

[전체 실행 순서 한눈에 보기]
  1. 명령어 파싱 (main.py)
  2. Git 변경 사항 수집 및 안전 모드 처리 (git_collector.py)
  3. AI에게 보낼 프롬프트 조립 (prompts.py)
  4. AI REST API 호출 (ai_client.py)
  5. 결과 검증 및 다듬기 후 화면 출력 (validator.py -> main.py)
"""

from __future__ import annotations

import argparse
import sys

# 우리가 역할별로 나눈 4개의 파일(모듈)에서 필요한 함수들을 불러옵니다.
from ai_client import call_ai_api, get_api_key
from git_collector import (
    apply_safe_mode,
    check_git_root_directory,
    collect_git_changes,
    get_current_branch,
)
from prompts import build_commit_prompt, build_pr_prompt
from validator import validate_and_refine_commit, validate_and_refine_pr


def build_arg_parser() -> argparse.ArgumentParser:
    """
    터미널에서 입력받는 명령어와 옵션을 설정하는 함수입니다.
    예: python3 example/main.py commit -temperature 0.3 -safe-mode
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Git 변경 사항(status, diff)을 수집해 커밋 메시지와 PR 초안을 자동 생성하는 AI CLI 도구",
    )

    # 1) 필수 위치 인자: 'commit' 또는 'pr' 중 하나를 반드시 입력해야 합니다.
    parser.add_argument(
        "command",
        choices=["commit", "pr"],
        help="실행할 작업 선택: 'commit' (커밋 메시지 생성) 또는 'pr' (PR 제목/본문 생성)",
    )

    # 2) 선택 옵션 인자: 입력하지 않으면 default(기본값)가 사용됩니다.
    parser.add_argument(
        "-model",
        "--model",
        default="gpt-4o-mini",
        help="사용할 AI 모델 이름 (기본값: gpt-4o-mini, Gemini 키 사용 시 gemini-2.0-flash 자동 호환)",
    )
    parser.add_argument(
        "-temperature",
        "--temperature",
        type=float,
        default=0.3,
        help="생성 결과의 무작위성/창의성 조절 (0.0 ~ 1.0, 기본값: 0.3)",
    )
    parser.add_argument(
        "-max-tokens",
        "--max-tokens",
        type=int,
        default=600,
        help="AI 응답의 최대 토큰 수 제한 (기본값: 600)",
    )
    parser.add_argument(
        "-safe-mode",
        "--safe-mode",
        action="store_true",
        help="안전 모드 활성화: diff 내 민감정보(API Key, 이메일 등) 마스킹 및 최대 10개 파일/200줄 제한",
    )

    return parser


def main() -> None:
    """프로그램이 시작될 때 가장 먼저 실행되는 메인 함수입니다."""
    # [1단계] CLI 명령어 및 옵션 읽기
    parser = build_arg_parser()
    args = parser.parse_args()

    # [2단계] 현재 폴더가 Git 저장소 루트인지 확인
    check_git_root_directory()

    # [3단계] Git 변경 사항(status, diff) 수집
    try:
        changed_files, diff_text = collect_git_changes()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # 변경된 파일이 없거나 diff가 비어 있으면 안내 메시지 출력 후 종료
    if not changed_files or not diff_text.strip():
        target_name = "커밋 메시지를" if args.command == "commit" else "PR 초안을"
        print(f"[INFO] 변경 사항이 없습니다. {target_name} 생성하지 않고 종료합니다.")
        sys.exit(0)

    # [4단계] AI API Key 환경변수 설정 여부 확인
    _ = get_api_key()

    # [5단계] 안전 모드(-safe-mode) 옵션이 켜져 있으면 마스킹 및 길이 제한 적용
    if args.safe_mode:
        print("[INFO] Safe Mode 활성화: 민감정보 마스킹 및 전송량 제한(최대 10개 파일, 200줄) 적용")
        changed_files, diff_text = apply_safe_mode(changed_files, diff_text)

    diff_line_count = len(diff_text.splitlines())
    api_call_count = 0

    # [6단계] 'commit' 또는 'pr' 명령에 따라 프롬프트 조립 -> AI 호출 -> 검증 -> 출력
    if args.command == "commit":
        print(f"[INFO] Git status 수집 완료: {len(changed_files)}개 파일 변경 감지")
        print(f"[INFO] Git diff 수집 완료: {diff_line_count}줄")
        print(
            f"[INFO] AI API 요청 중... "
            f"(model={args.model}, temperature={args.temperature}, max_tokens={args.max_tokens})"
        )

        system_prompt, user_prompt = build_commit_prompt(changed_files, diff_text)
        raw_response = call_ai_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        api_call_count += 1

        commit_message = validate_and_refine_commit(raw_response, changed_files)
        print(f"[DONE] 커밋 메시지 생성 완료 (AI API 호출 횟수: {api_call_count}회)\n")
        print("--- Commit Message ---")
        print(commit_message)
        print("----------------------")

    elif args.command == "pr":
        branch_name = get_current_branch()
        print(f"[INFO] 현재 브랜치: {branch_name}")
        print(f"[INFO] Git status 수집 완료: {len(changed_files)}개 파일 변경 감지")
        print(f"[INFO] Git diff 수집 완료: {diff_line_count}줄")
        print(
            f"[INFO] AI API 요청 중... "
            f"(model={args.model}, temperature={args.temperature}, max_tokens={args.max_tokens})"
        )

        system_prompt, user_prompt = build_pr_prompt(branch_name, changed_files, diff_text)
        raw_response = call_ai_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        api_call_count += 1

        pr_title, pr_body = validate_and_refine_pr(raw_response, changed_files)
        print(f"[DONE] PR 초안 생성 완료 (AI API 호출 횟수: {api_call_count}회)\n")
        print("--- PR Title ---")
        print(pr_title)
        print("\n--- PR Body ---")
        print(pr_body)
        print("---------------")


if __name__ == "__main__":
    main()
