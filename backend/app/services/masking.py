"""발화에서 개인정보를 가린다.

업로드된 상담 기록에는 실명, 연락처 등이 섞일 수 있으므로
DB에 저장하기 전에 이 단계를 반드시 거친다.
"""

import re

PATTERNS = [
    # 주민등록번호
    (re.compile(r"\d{6}\s*[-–]\s*[1-4]\d{6}"), "[주민번호]"),
    # 전화번호
    (re.compile(r"0\d{1,2}[-–.\s]?\d{3,4}[-–.\s]?\d{4}"), "[전화번호]"),
    # 이메일
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[이메일]"),
    # 계좌번호로 보이는 숫자열
    (re.compile(r"\b\d{2,6}[-–]\d{2,6}[-–]\d{2,8}\b"), "[계좌번호]"),
    # 주소
    (re.compile(r"[가-힣]+(시|도)\s*[가-힣]+(구|군|시)\s*[가-힣0-9]+(동|읍|면)"), "[주소]"),
]


def mask_text(text: str, names: list[str] | None = None) -> str:
    """한 발화에서 개인정보를 가린다."""
    for name in names or []:
        if len(name) >= 2:
            text = text.replace(name, "[이름]")

    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def mask_utterances(rows: list[dict], names: list[str] | None = None) -> list[dict]:
    """발화 목록 전체에 마스킹을 적용한다."""
    return [{**r, "text": mask_text(r["text"], names)} for r in rows]