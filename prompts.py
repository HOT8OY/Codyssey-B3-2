"""
수집한 Git 변경 사항(파일 목록, diff)을 바탕으로
AI가 미션 규치겡 맞게 답변하도록 프롬프트(지시문)를 조립합니다.
"""

from __future__ import annotations

from typing import List, Tuple

def build_commit_prompt(changed_files: List[str], diff_text: str) -> Tuple[str, str]:
    """
    커밋 메시지 생성을 위한 System 프롬프트(AI의 역할과 작성 규칙)와
    User 프롬프트(실제 변경된 파일 목록과 diff 데이터)를 만들어 반환합니다.
    """
    system_prompt = (
        "당신은 숙력된 소프트웨어 엔지니어입니다. "
        "주어진 Git 변경 파일 목록과 git diff 내용을 분석하여 한국어로 명확한 Git 커밋 메시지를 작성해세요.\n\n"
        "[출력 규칙 - 반드시 준수할 것]\n"
        "1. 첫 번째 줄은 커밋 제목(1줄)으로 작성하며, Conventional Coomits 형식(feat:, fix:, docs:, refactor:, chore: 둥)을 사용하세요.\n"
        "2. 커밋 제목은 50자 이낼르 권장하며, 절대 72자를 넘지 마세요.\n"
        "3. 두 번쨰 줄은 반드시 빈 줄로 비워두세요.\n"
        "4. 세 번째 줄부터는 커밋 본문을 불릿('- ') 형식으로 2~3줄 작성하세요.\n"
        "5. 커밋 본문에는 변경된 주요 파일(1~3개)과 핵심 변경 사항 요약을 반드시 포함하세요.\n"
        "6. 마크다운 코드 블록(```)이나 불필요한 인사말 없이 오직 커밋 메시지 원문만 출력하세요."
    )

    files_str = "\n".join(f"- {file}" for file in changed_files)
    user_prompt = (
        f"[변경된 파일 목록 ({len(changed_files)}개)]\n"
        f"{files_str}\n\n"
        f"[Git Diff 내용]\n"
        f"{diff_text}"
    )
    return system_prompt, user_prompt

def build_pr_prompt(branch_name: str, changed_files: List[str], diff_text: str) -> Tuple[str, str]:
    """
    Pull Request 제목 및 본문 초안 생성을 위한 프롬프트를 조립합니다.
    """
    system_prompt = (
        "당신은 숙련된 소프트웨어 엔지니어입니다. "
        "주어진 Git 브랜치명, 변경 파일 목록, git diff 내용을 분석하여 한국어로 Pull Request(PR) 제목과 본문 초안을 작성하세요.\n\n"
        "[출력 규칙 - 반드시 아래 형식을 정확히 지킬 것]\n"
        "1. 첫 번째 줄에는 'TITLE: '로 시작하는 1줄짜리 PR 제목(최대 80자 이내, 예: TITLE: feat: 커밋/PR 자동 생성 기능 추가)을 작성하세요.\n"
        "2. 두 번째 줄부터는 아래 3개의 마크다운 섹션 헤더를 정확한 이름으로 포함하여 PR 본문을 작성하세요.\n"
        "   ## Why\n"
        "   ## What\n"
        "   ## How to Test\n"
        "3. 각 섹션(Why, What, How to Test) 아래에는 반드시 최소 1개 이상의 불릿('- ')을 포함하세요.\n"
        "   - Why: 변경 배경 및 목적\n"
        "   - What: 핵심 변경 사항 요약\n"
        "   - How to Test: 이 변경 사항을 테스트하고 검증하는 구체적인 방법\n"
        "4. 마크다운 코드 블록(```)으로 전체를 감싸지 말고 바로 출력하세요."
    )

    files_str = "\n".join(f"- {file}" for file in changed_files)
    user_prompt = (
        f"[현재 브랜치]\n{branch_name}\n\n"
        f"[변경된 파일 목록 ({len(changed_files)}개)]\n"
        f"{files_str}\n\n"
        f"[Git Diff 내용]\n"
        f"{diff_text}"
    )
    return system_prompt, user_prompt