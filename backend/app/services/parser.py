"""
대화 기록 파일을 발화 시퀀스로 변환한다.

지원 형식
    - 축어록 txt : "상담자: 안녕하세요" 형태
    - CSV        : 화자/발화 컬럼
    - 카카오톡   : 내보내기 txt (PC/모바일)

모든 형식이 동일한 결과를 돌려준다.
    [{"index": 1, "speaker": "내담자", "text": "..."}, ...]
"""

import csv
import io
import re

MERGE_LIMIT = 3      # 같은 화자의 연속 발화를 최대 몇 개까지 합칠지
MIN_UTTERANCES = 5   # 이보다 적으면 분석할 수 없다고 본다


class ParseError(Exception):
    """파일 형식을 인식하지 못했을 때."""


# ── 형식별 패턴 ──────────────────────────────────────

# 축어록: "상담자: 내용" / "상담자 : 내용" / "[상담자] 내용"
TRANSCRIPT_RE = re.compile(r"^\[?([^\[\]:：]{1,20})\]?\s*[:：]\s*(.*)$")

# 카톡 PC: "[김상담] [오후 2:01] 내용"
KAKAO_PC_RE = re.compile(r"^\[([^\]]+)\]\s*\[[^\]]+\]\s*(.*)$")

# 카톡 모바일: "2026년 9월 1일 오후 2:01, 김상담 : 내용"
KAKAO_MOBILE_RE = re.compile(r"^\d{4}[.년].*?,\s*([^:]+?)\s*:\s*(.*)$")

# 건너뛸 줄 (날짜 구분선, 입퇴장 알림 등)
SKIP_RE = re.compile(r"^(-+\s*\d{4}|저장한 날짜|.*님이 들어왔습니다|.*님이 나갔습니다)")


def parse(content: bytes | str, filename: str = "") -> list[dict]:
    """파일 내용을 발화 목록으로 변환한다."""
    text = _decode(content) if isinstance(content, bytes) else content

    if filename.lower().endswith(".csv"):
        rows = _parse_csv(text)
    else:
        rows = _parse_text(text)

    if len(rows) < MIN_UTTERANCES:
        raise ParseError(
            f"발화를 {len(rows)}개만 찾았습니다. 파일 형식을 확인해 주세요."
        )

    rows = _merge_consecutive(rows)

    for i, row in enumerate(rows, 1):
        row["index"] = i
    return rows


def _decode(raw: bytes) -> str:
    """인코딩을 추정해 글자로 바꾼다."""
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _parse_csv(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ParseError("CSV에 머리글이 없습니다.")

    speaker_col = _find_column(reader.fieldnames, ["화자", "speaker", "이름"])
    text_col = _find_column(reader.fieldnames, ["발화", "내용", "text", "message"])
    if not speaker_col or not text_col:
        raise ParseError("CSV에 화자/발화 열을 찾지 못했습니다.")

    rows = []
    for row in reader:
        speaker = (row.get(speaker_col) or "").strip()
        content = (row.get(text_col) or "").strip()
        if speaker and content:
            rows.append({"speaker": speaker, "text": content})
    return rows


def _find_column(fieldnames: list[str], candidates: list[str]) -> str | None:
    for name in fieldnames:
        if name and name.strip().lower() in candidates:
            return name
    return None


def _parse_text(text: str) -> list[dict]:
    """축어록과 카톡을 같은 방식으로 훑는다."""
    rows: list[dict] = []

    for line in text.splitlines():
        line = line.strip()
        if not line or SKIP_RE.match(line):
            continue

        matched = (
            KAKAO_PC_RE.match(line)
            or KAKAO_MOBILE_RE.match(line)
            or TRANSCRIPT_RE.match(line)
        )

        if matched:
            speaker = matched.group(1).strip()
            content = matched.group(2).strip()
            if content:
                rows.append({"speaker": speaker, "text": content})
        elif rows:
            # 화자 표시가 없는 줄 = 앞 발화가 이어지는 내용
            rows[-1]["text"] += " " + line

    return rows


def _merge_consecutive(rows: list[dict]) -> list[dict]:
    """같은 화자가 연달아 말한 발화를 하나로 합친다.

    메신저는 한 문장을 여러 번에 나눠 보내는 일이 많다.
    따로 분석하면 "아", "근데" 같은 조각의 감정을 묻게 되므로 합친다.
    """
    merged: list[dict] = []
    run = 0

    for row in rows:
        if merged and merged[-1]["speaker"] == row["speaker"] and run < MERGE_LIMIT:
            merged[-1]["text"] += " " + row["text"]
            run += 1
        else:
            merged.append(dict(row))
            run = 1
    return merged


def get_speakers(rows: list[dict]) -> list[str]:
    """파일에 등장하는 화자 이름을 순서대로 돌려준다."""
    return list(dict.fromkeys(r["speaker"] for r in rows))


def map_speakers(rows: list[dict], counselor: str | None = None) -> list[dict]:
    """원래 화자 이름을 상담자/내담자로 바꾼다.

    1) 이미 상담자/내담자로 적혀 있으면 그대로 둔다.
    2) counselor를 지정하면 그 사람을 상담자로 본다.
    3) 둘 다 아니면 먼저 말한 사람을 상담자로 본다.
    """
    names = get_speakers(rows)
    mapping: dict[str, str] = {}

    for name in names:
        if name in ("상담자", "내담자"):
            mapping[name] = name

    rest = [n for n in names if n not in mapping]

    if counselor and counselor in rest:
        for name in rest:
            mapping[name] = "상담자" if name == counselor else "내담자"
    elif rest:
        if "상담자" in mapping.values():
            for name in rest:
                mapping[name] = "내담자"
        else:
            mapping[rest[0]] = "상담자"
            for name in rest[1:]:
                mapping[name] = "내담자"

    return [{**r, "speaker": mapping[r["speaker"]]} for r in rows]