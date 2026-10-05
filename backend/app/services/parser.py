"""
대화 기록 파일을 발화 목록으로 변환한다.

지원 형식
    - 축어록 txt : "상담자 28: 내용", "상1: 내용" 등
    - CSV        : 화자/발화 컬럼
    - 카카오톡   : 내보내기 txt (현 수준에서 유지, 추가 처리 없음)

결과
    [{"index": 1, "speaker": "상담자", "text": "원문 그대로"}, ...]

원문(text)에는 괄호류 지문이 그대로 남는다.
줄 전체가 지문이면 직전 발화의 원문 끝에 이어 붙인다.
분석용 텍스트는 text_rules.clean_text()로 그때그때 만든다.
"""

import csv
import io
import re

from app.services.text_rules import CLOSERS_RE, OPENERS, is_whole_bracket, normalize_dots

MERGE_LIMIT = 3      # 같은 화자의 연속 발화를 최대 몇 개까지 합칠지
MIN_UTTERANCES = 5   # 이보다 적으면 분석할 수 없다고 본다


class ParseError(Exception):
    """파일 형식을 인식하지 못했을 때."""


# ── 형식별 패턴 ──────────────────────────────────────

# 축어록: "상담자 28: 내용" / "상1 : 내용" / "[상담자]: 내용"
TRANSCRIPT_RE = re.compile(r"^\[?([^\[\]:：(（{]{1,20})\]?\s*[:：]\s*(.*)$")

# 카톡 PC: "[김상담] [오후 2:01] 내용"
KAKAO_PC_RE = re.compile(r"^\[([^\]]+)\]\s*\[[^\]]+\]\s*(.*)$")

# 카톡 모바일: "2026년 9월 1일 오후 2:01, 김상담 : 내용"
KAKAO_MOBILE_RE = re.compile(r"^\d{4}[.년].*?,\s*([^:]+?)\s*:\s*(.*)$")

# 건너뛸 줄 (카톡 날짜 구분선, 입퇴장 알림 등)
SKIP_RE = re.compile(r"^(-+\s*\d{4}|저장한 날짜|.*님이 들어왔습니다|.*님이 나갔습니다)")

# 화자 이름 뒤 번호 제거: "상담자 28" -> "상담자"
SPEAKER_NUM_RE = re.compile(r"[\s\-_]*\d+\s*$")

# 역할 표기 통일
ROLE_ALIASES = {
    "상담자": "상담자", "상담사": "상담자", "치료자": "상담자",
    "상담": "상담자", "상": "상담자", "T": "상담자", "t": "상담자",
    "내담자": "내담자", "내담": "내담자", "환자": "내담자",
    "내": "내담자", "C": "내담자", "c": "내담자",
}


def normalize_speaker(name: str) -> str:
    """화자 표기를 정리한다. 번호를 떼고 역할 이름을 통일한다."""
    name = SPEAKER_NUM_RE.sub("", name.strip())
    return ROLE_ALIASES.get(name, name)


# ── 진입점 ───────────────────────────────────────────

def parse(content: bytes | str, filename: str = "") -> list[dict]:
    """파일 내용을 발화 목록으로 변환한다."""
    text = _decode(content) if isinstance(content, bytes) else content
    text = normalize_dots(text)

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


# ── CSV ──────────────────────────────────────────────

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
            rows.append({"speaker": normalize_speaker(speaker), "text": content})
    return rows


def _find_column(fieldnames: list[str], candidates: list[str]) -> str | None:
    for name in fieldnames:
        if name and name.strip().lower() in candidates:
            return name
    return None


# ── 축어록 / 카톡 ────────────────────────────────────

def _parse_text(text: str) -> list[dict]:
    rows: list[dict] = []
    pending: str | None = None   # 여러 줄에 걸친 지문을 모으는 중

    for line in text.splitlines():
        line = line.strip()

        # 여러 줄 지문: 닫는 괄호가 나올 때까지 모아서 직전 발화에 붙인다
        if pending is not None:
            pending += " " + line
            if CLOSERS_RE.search(line):
                _append_to_last(rows, pending)
                pending = None
            continue

        if not line or SKIP_RE.match(line):
            continue

        # 줄 전체가 지문이면 직전 발화 원문 끝에 붙인다
        if line[0] in OPENERS:
            if is_whole_bracket(line):
                _append_to_last(rows, line)
                continue
            if not CLOSERS_RE.search(line):
                pending = line
                continue

        matched = (
            KAKAO_PC_RE.match(line)
            or KAKAO_MOBILE_RE.match(line)
            or TRANSCRIPT_RE.match(line)
        )

        if matched:
            speaker = normalize_speaker(matched.group(1))
            content = matched.group(2).strip()
            if content:
                rows.append({"speaker": speaker, "text": content})
        else:
            # 화자 표시가 없는 줄 = 앞 발화가 이어지는 내용
            _append_to_last(rows, line)

    if pending is not None:          # 끝까지 안 닫힌 지문
        _append_to_last(rows, pending)

    return rows


def _append_to_last(rows: list[dict], text: str) -> None:
    if rows:
        rows[-1]["text"] += " " + text


# ── 후처리 ───────────────────────────────────────────

def _merge_consecutive(rows: list[dict]) -> list[dict]:
    """같은 화자가 연달아 말한 발화를 하나로 합친다."""
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
    """화자 이름을 상담자/내담자로 바꾼다.

    1) 이미 상담자/내담자면 그대로 둔다.
    2) counselor를 지정하면 그 사람을 상담자로 본다.
    3) 둘 다 아니면 먼저 말한 사람을 상담자로 본다.
    """
    names = get_speakers(rows)
    mapping: dict[str, str] = {n: n for n in names if n in ("상담자", "내담자")}
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