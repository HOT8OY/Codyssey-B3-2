"""
[모듈 4: validator.py]
역할: AI가 생성한 커밋 메시지와 PR 초안이 실무 규칙(글자 수 제한, 필수 섹션, 불릿 포함 여부)을
      지켰는지 검사하고, 부족한 부분이 있으면 자동으로 다듬어 주는(후처리) 모듈입니다.
"""

from __future__ import annotations

import re
from typing import List, Tuple


def strip_markdown_code_fence(text: str) -> str:
    """
    AI가 가끔 답변 위아래에 ``` 같은 마크다운 코드 블록 기호를 붙여서 줄 때가 있는데,
    이를 깔끔하게 벗겨내는 보조 함수입니다.
    """
    lines = text.strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
        return "\n".join(lines[1:-1]).strip()
    return text.strip()


def validate_and_refine_commit(raw_text: str, changed_files: List[str]) -> str:
    """
    커밋 메시지 검증 및 다듬기 함수입니다. (미션 요구사항 4-3, 4-5)
    - 규칙 1: 커밋 제목 1줄 필수, 최대 72자 이내 (50자 이내 권장)
    - 규칙 2: 본문에 불릿('- ') 요약 및 변경 파일 언급 포함
    """
    cleaned = strip_markdown_code_fence(raw_text)
    lines = [line.rstrip() for line in cleaned.splitlines()]

    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        title = "chore: 코드 변경 사항 반영"
        body_lines: List[str] = []
    else:
        title = non_empty_lines[0].strip()
        first_idx = lines.index(non_empty_lines[0])
        body_lines = lines[first_idx + 1 :]

    # [검증 1] 제목이 72자를 넘으면 72자 이내로 잘라줍니다.
    if len(title) > 72:
        title = title[:69].rstrip() + "..."

    # 본문 위아래의 불필요한 빈 줄 제거
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    # [검증 2] 본문에 불릿('- ' 또는 '* ')이 하나도 없으면 기본 변경 파일 불릿을 추가합니다.
    has_bullet = any(line.strip().startswith(("-", "*")) for line in body_lines)
    if not has_bullet:
        sample_files = ", ".join(changed_files[:3])
        body_lines.append(f"- 변경된 주요 파일: {sample_files}")

    return title + "\n\n" + "\n".join(body_lines)


def validate_and_refine_pr(
    raw_text: str,
    changed_files: List[str],
) -> Tuple[str, str]:
    """
    PR 제목/본문 검증 및 다듬기 함수입니다. (미션 요구사항 4-4, 4-5)
    - 규칙 1: PR 제목 1줄, 최대 80자 이내
    - 규칙 2: PR 본문에 `## Why`, `## What`, `## How to Test` 섹션 헤더 필수 포함
    - 규칙 3: 각 섹션마다 최소 1개 이상의 불릿('- ') 필수 포함
    """
    cleaned = strip_markdown_code_fence(raw_text)
    lines = cleaned.splitlines()

    pr_title = ""
    body_start_idx = 0

    # 1) 첫 줄에서 PR 제목 분리하기
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.upper().startswith("TITLE:"):
            pr_title = stripped[6:].strip()
            body_start_idx = idx + 1
            break
        elif not stripped.startswith("##"):
            pr_title = stripped.lstrip("#").strip()
            body_start_idx = idx + 1
            break
        else:
            pr_title = f"feat: {changed_files[0]} 등 {len(changed_files)}개 파일 변경 사항 반영"
            body_start_idx = idx
            break

    if not pr_title:
        pr_title = f"feat: {len(changed_files)}개 파일 변경 사항 반영"

    # [검증 1] PR 제목 최대 80자 제한
    if len(pr_title) > 80:
        pr_title = pr_title[:77].rstrip() + "..."

    pr_body = "\n".join(lines[body_start_idx:]).strip()

    # [검증 2 & 3] 필수 섹션 헤더 3개와 각 섹션의 불릿이 있는지 확인하고, 누락 시 자동 보충
    required_sections = [
        ("Why", "- 코드 변경 사항을 반영하고 기능을 개선하기 위해 작업했습니다."),
        ("What", f"- 주요 변경 파일({', '.join(changed_files[:3])}) 수정 사항 반영"),
        ("How to Test", "- 로컬 환경에서 변경된 기능 실행 및 정상 동작 여부 확인"),
    ]

    for section_name, fallback_bullet in required_sections:
        header_pattern = re.compile(
            rf"^##+\s*{re.escape(section_name)}\b",
            re.IGNORECASE | re.MULTILINE,
        )
        match = header_pattern.search(pr_body)

        if not match:
            # 해당 섹션 헤더가 아예 없으면 본문 끝에 추가
            pr_body = pr_body.rstrip() + f"\n\n## {section_name}\n{fallback_bullet}"
        else:
            # 섹션 헤더는 있지만 아래에 불릿('- ')이 없는 경우 기본 불릿 추가
            start_pos = match.end()
            next_header = re.search(r"^##+\s+", pr_body[start_pos:], re.MULTILINE)
            section_content = (
                pr_body[start_pos : start_pos + next_header.start()]
                if next_header
                else pr_body[start_pos:]
            )
            # 오려낸 구간 안에 불릿(- 또는 *)이 있는지 검사
            has_bullet = any(
                line.strip().startswith(("-", "*"))
                for line in section_content.splitlines()
            )
            # 불릿이 없으면 제목 바로 아랫줄에 끼워 넣기
            if not has_bullet:
                pr_body = (
                    pr_body[:start_pos]
                    + f"\n{fallback_bullet}"
                    + pr_body[start_pos:]
                )

    return pr_title, pr_body.strip()

