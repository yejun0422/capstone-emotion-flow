"""발화에서 개인정보를 가린다.

업로드된 상담 기록에는 실명, 연락처 등이 섞일 수 있으므로
DB에 저장하기 전에 이 단계를 반드시 거친다.

가림 표시는 〈 〉를 쓴다. [ ]나 ( )를 쓰면 text_rules가
비언어 정보로 오인해 분석에서 빼고 화면에서 회색 처리하기 때문이다.
"""

import re

ROLE_NAMES = {"상담자", "내담자"}

PATTERNS = [
    (re.compile(r"\d{6}\s*[-–]\s*[1-4]\d{6}"), "〈주민번호〉"),
    (re.compile(r"0\d{1,2}[-–.\s]?\d{3,4}[-–.\s]?\d{4}"), "〈전화번호〉"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "〈이메일〉"),
    (re.compile(r"\b\d{2,6}[-–]\d{2,6}[-–]\d{2,8}\b"), "〈계좌번호〉"),
    (re.compile(r"[가-힣]+(시|도)\s*[가-힣]+(구|군|시)\s*[가-힣0-9]+(동|읍|면)"), "〈주소〉"),
]


def mask_text(text: str, names: list[str] | None = None) -> str:
    """한 발화에서 개인정보를 가린다."""
    for name in names or []:
        # 역할 이름은 실명이 아니므로 가리지 않는다
        if len(name) >= 2 and name not in ROLE_NAMES:
            text = text.replace(name, "〈이름〉")

    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def mask_utterances(rows: list[dict], names: list[str] | None = None) -> list[dict]:
    """발화 목록 전체에 마스킹을 적용한다."""
    return [{**r, "text": mask_text(r["text"], names)} for r in rows]