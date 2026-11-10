"""
Git 명령어(git status, git diff)를 실행해 변경 사항을 수집하고,
    안전모드(-safe-mode)일 때 민감정보를 가리는(마스킹) 역할을 담당.
"""

from __future__ import annotations # 파이썬 구버전 호환용, 모든 import문보다 상단에 위치해야 함

import os
import re
import subprocess
import sys
from typing import List, Tuple 

def run_git_command(args: List[str]) -> str:
    """
    터미널에서 직접 치던 `git ...`명령어를 파이썬이 대신 실행하고,
    화면에 출력되는 글자(stdout)를 문자열로 받아오는 함수.
    """
    # - subprocess.run(["git", "status"], ...): 터미널에 `git status`를 친 것과 같습니다.
    # - capture_output=True: 결과를 화면에 바로 뿌리지 않고 파이썬 변수(result.stdout)에 담습니다.
    # - text=True: 컴퓨터용 바이트(0과 1)가 아니라 사람이 읽는 문자열(str)로 변환해 줍니다.
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        print("[ERROR] 시스템에 'git'이 설치되어 있지 않거나 PATH에 없습니다.")
        sys.exit(1)
    
    # returncode가 0이면 성공, 0이 아니면 에러가 발생한 것.
    if result.returncode != 0:
        err_msg = result.stderr.strip() or "알 수 없는 Git 오류"
        raise RuntimeError(f"Git 명령어 실행 실패 (git{' '.join(args)}): {err_msg}")
    
    return result.stdout

def check_git_root_directory() -> None:
    """
    현재 터미널 위치가 Git이 초기화된 프로젝트 폴더인지 확인합니다.
    """
    try:
        top_level = run_git_command(["rev-parse", "--show-toplevel"]).strip()
        current_dir = os.path.abspath(os.getcwd())
        if os.path.abspath(top_level) != current_dir:
            print(
                f"[WARNING] 현재 위치가 Git 루트 디렉토리가 아닙니다.\n"
                f"  - 현재 위치: {current_dir}\n"
                f"  - Git 루트: {top_level}"
            )
    except RuntimeError:
        print(
            "[ERROR] 현재 디렉토리는 Git 저장소가 아닙니다. "
            "'git init'을 먼저 수행하거나 프로젝트 루트에서 실행하세요."
        )
        sys.exit(1)

def get_current_branch() -> str:
    """현재 작업 중인 Git 브랜치 이름을 가져옵니다 (예: main, feature/login)."""
    try:
        branch = run_git_command(["branch", "--show-current"]).strip()
        return branch if branch else "HEAD (detached)"
    except RuntimeError:
        return "unknown"

def collect_git_changes() -> Tuple[List[str], str]:
    """
    `git status`로 변경된 파일 이름 목록을 모으고,
    `git diff`로 어떤 코드가 수정되었는지 상세 텍스트를 모아서 반환합니다.
    """
    # 1) 변경된 파일 목록 수집 (`git status --porcelain -uall`)
    status_output = run_git_command(["status", "--porcelain", "-uall"])
    changed_files: List[str] = []

    for line in status_output.splitlines():
        if not line.strip():
            continue
    # 앞의 3글자(예: " M ", "?? ")를 잘라내고 파일 경로만 추출합니다.
        file_path = line[3:].strip()
        changed_files.append(file_path)
    
    # 2) 상세 코드 변경 내용 수집(`git diff`)
    # 아직 `git add` 안 한 변경사항(unstaged)과 `git add` 한 변경 사항(staged)을 모두 가져옵니다.
    unstaged_diff = run_git_command(["diff"])
    staged_diff = run_git_command(["diff", "--cached"])

    combined_diff_parts: List[str] = []
    if staged_diff.strip():
        combined_diff_parts.append("# [Staged Changes (git diff --cached)]\n" + staged_diff.strip())
    if unstaged_diff.strip():
        combined_diff_parts.append("# [Unstaged Changes (git diff)]\n" + unstaged_diff.strip())
    
    diff_text = "\n\n".join(combined_diff_parts)

    # 새로 만든 파일(Untracked, ??)만 있을 때는 git diff 결과가 비어있으므로 파일 목록을 대신 넣어줍니다.
    if changed_files and not diff_text.strip():
        diff_text = (
            "# 새로 추가된 파일(Untracked files) 등으로 인해 상세 텍스트 diff가 비어있습니다.\n"
            "# 변경된 파일 목록:\n" + "\n".join(f"- {f}" for f in changed_files)
        )
    
    return changed_files, diff_text

def apply_safe_mode(
    changed_files: List[str],
    diff_text: str,
    max_files: int = 10,
    max_lines: int = 200,
) -> Tuple[List[str], str]:
    """
    `-safe-mode` 옵션을 켰을 때 동작하는 보안함수입니다.
    1) 이메일, API 키, 비밀번호 같은 민감정보를 `[MASKED_*]`로 가립니다.
    2) 파일은 최대 10개, diff 줄 수는 최대 200줄까지만 잘라서 전송량을 제한합니다.
    """
    # 1. 파일 개수 제한 (리스트 슬라이싱 활용)
    safe_files = changed_files[:max_files]

    # 2. 정규표현식(re.sub)을 이용한 민감정보 마스킹
    masked_diff = diff_text

    # (1) 이메일 주소 가리기
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    masked_diff = re.sub(email_pattern, "[MASKED_EMAIL]", masked_diff)

    # (2) 대표 API Key 형태 가리기 (OpenAI 'sk-...', Google 'AQ.Ab...' / 'AIza...', GitHub 'ghp_...')
    token_pattern = r"\b(sk-[a-zA-Z0-9_-]{15,}|AQ\.[0-9A-Za-z._-]{15,}|AIza[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z]{20,})\b"
    masked_diff = re.sub(token_pattern, "[MASKED_API_KEY]", masked_diff)

    # (3) 코드 내 변수 할당 형태 가리기 (예: password = "1234" -> password = "[MASKED_SECRET]")
    secret_assign_pattern = (
        r"(?i)((?:api[_-]?key|secret|password|token|passwd)\s*[:=]\s*['\"])([^'\"]+)(['\"])"
    )
    masked_diff = re.sub(secret_assign_pattern, r"\1[MASKED_SECRET]\3", masked_diff)

    # 3. diff 줄 수 제한 (최대 200줄)
    diff_lines = masked_diff.splitlines()
    if len(diff_lines) > max_lines:
        masked_diff = "\n".join(diff_lines[:max_lines])
        masked_diff += f"\n\n... [SAFE-MODE: 총 {len(diff_lines)}줄 중 {max_lines}줄까지만 전송됨] ..."
    
    return safe_files, masked_diff