"""
발화 텍스트 정리 규칙.

괄호류(소·중·대괄호, 별표 하나로 감싼 것)는 비언어 정보나 끼어든 상대 발화로 보고
감정 분석에서 제외한다. 원문은 그대로 저장하고, 분석 직전에만 떼어낸다.

※ frontend/src/constants/nonverbal.ts 의 NONVERBAL_RE 와 반드시 같이 수정할 것.
   (프론트는 같은 규칙으로 화면에서 회색 처리한다)
"""

import re

# 비언어 표시
#   (( ))  ( )  （ ）  [ ]  { }  *한숨*
#   별표가 2개 이상 연속(***)이면 이름 가림이므로 건드리지 않는다
NONVERBAL_RE = re.compile(
    r"\(\([^()]*\)\)"
    r"|\([^()]*\)"
    r"|（[^（）]*）"
    r"|\[[^\[\]]*\]"
    r"|\{[^{}]*\}"
    r"|(?<!\*)\*(?!\*)[^*\n]+?(?<!\*)\*(?!\*)"
)

OPENERS = "([{（"
CLOSERS_RE = re.compile(r"[)\]}）]")

MIN_LENGTH = 5          # 분석에 필요한 최소 글자 수
HAS_WORD_RE = re.compile(r"[가-힣A-Za-z0-9]")


def normalize_dots(text: str) -> str:
    """특수 말줄임 문자를 일반 마침표로 바꾼다. 말줄임 자체는 남긴다."""
    return text.replace("\u2024", ".").replace("\u2026", "...")


def is_whole_bracket(line: str) -> bool:
    """줄 전체가 괄호 하나로 감싸져 있는가."""
    return NONVERBAL_RE.fullmatch(line) is not None


def clean_text(text: str) -> str:
    """분석용 텍스트: 괄호류를 떼어낸다."""
    return re.sub(r"\s+", " ", NONVERBAL_RE.sub(" ", text)).strip()


def is_analyzable(clean: str) -> bool:
    """분석할 만한 내용이 남아 있는가. 지문만 있거나 너무 짧으면 False."""
    return bool(HAS_WORD_RE.search(clean)) and len(clean) >= MIN_LENGTH