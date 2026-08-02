"""Fake-text-conversation renderer: a chat plays out in bubbles with typing beats.

Not a narration timeline — the script's segments ARE the messages ("A: hey").
The whole conversation is rendered as ASS subtitle events over one looped
background clip: each state of the chat (bubbles visible + their positions)
is a set of Dialogue events for that time interval. BorderStyle=3 draws the
bubble boxes; libass does the compositing, so no per-frame image work.
"""
import re
from pathlib import Path

# Seconds of "•••" typing indicator before each message lands.
TYPING_BEAT = 0.8
# Reading dwell after a message appears before the next typing starts.
MIN_DWELL = 1.1
DWELL_PER_WORD = 0.34
TAIL = 2.5          # hold the finished conversation on screen
MAX_DURATION = 85.0  # hard cap — tighten dwell if the chat would run long

WRAP_CHARS = 24     # manual wrap width (ASS \pos disables auto-wrapping)

_HEADER_TMPL = """[Script Info]
ScriptType: v4.00+
PlayResX: {play_x}
PlayResY: {play_y}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: BubbleA,Arial,{fontsize},&H00FFFFFF,&H00FFFFFF,&H003A3A3A,&H00000000,0,0,0,0,100,100,0,0,3,{pad},0,7,0,0,0,1
Style: BubbleB,Arial,{fontsize},&H00FFFFFF,&H00FFFFFF,&H00F27D34,&H00000000,0,0,0,0,100,100,0,0,3,{pad},0,9,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def parse_messages(segments: list[dict]) -> list[dict]:
    """Segments -> [{"speaker": "A"|"B", "text": str}]. The recipe asks the
    LLM to prefix each message with 'A:'/'B:'; alternate as a fallback."""
    messages = []
    for i, seg in enumerate(segments):
        raw = str(seg.get("text") or "").strip()
        if not raw:
            continue
        m = re.match(r"^\s*([AB])\s*[:\-–]\s*(.+)$", raw, re.DOTALL | re.IGNORECASE)
        if m:
            speaker, text = m.group(1).upper(), m.group(2).strip()
        else:
            speaker, text = ("A", "B")[i % 2], raw
        messages.append({"speaker": speaker, "text": text})
    return messages


def _wrap(text: str, width: int = WRAP_CHARS) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def build_timeline(messages: list[dict]) -> list[dict]:
    """[{speaker, text, typing_at, at}] with a typing beat before each message.
    Dwell scales with message length; the whole chat is capped at MAX_DURATION."""
    def make(dwell_scale: float) -> tuple[list[dict], float]:
        t, out = 0.6, []
        for m in messages:
            typing_at = t
            at = typing_at + TYPING_BEAT
            out.append({**m, "typing_at": round(typing_at, 2), "at": round(at, 2)})
            dwell = max(MIN_DWELL, DWELL_PER_WORD * len(m["text"].split())) * dwell_scale
            t = at + dwell
        return out, t + TAIL

    timeline, total = make(1.0)
    if total > MAX_DURATION:
        timeline, total = make(max(0.4, MAX_DURATION / total))
    return timeline, round(min(total, MAX_DURATION), 2)


def _ass_time(seconds: float) -> str:
    seconds = max(seconds, 0.0)
    h, m, s = int(seconds // 3600), int(seconds % 3600 // 60), seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def write_chat_ass(
    messages: list[dict],
    out_path: Path,
    play_res: tuple[int, int] = (1080, 1920),
) -> tuple[Path, float]:
    """Emit the chat as piecewise-static ASS states; returns (path, duration)."""
    px, py = play_res
    s = py / 1920
    fontsize = max(20, round(54 * s))
    pad = max(8, round(18 * s))
    line_h = round(fontsize * 1.32)
    gap = round(22 * s)
    margin_x = round(60 * (px / 1080))
    chat_bottom = round(py * 0.82)
    chat_top = round(py * 0.16)

    timeline, total = build_timeline(messages)

    # Event boundaries: every typing start and message arrival changes state.
    boundaries = sorted({e["typing_at"] for e in timeline} | {e["at"] for e in timeline})
    boundaries.append(total)

    def bubble_height(text: str) -> int:
        return len(_wrap(text)) * line_h + pad * 2

    events = []
    for k in range(len(boundaries) - 1):
        t0, t1 = boundaries[k], boundaries[k + 1]
        if t1 - t0 < 0.01:
            continue
        # Visible chat state during [t0, t1): landed messages + maybe a typing bubble.
        landed = [e for e in timeline if e["at"] <= t0]
        typing = next((e for e in timeline if e["typing_at"] <= t0 < e["at"]), None)
        stack = [{"speaker": e["speaker"], "text": e["text"]} for e in landed]
        if typing is not None:
            stack.append({"speaker": typing["speaker"], "text": "• • •"})
        # Fit from the bottom up; older messages scroll off the top.
        placed = []
        y = chat_bottom
        for item in reversed(stack):
            h = bubble_height(item["text"])
            y -= h
            if y < chat_top:
                break
            placed.append((y, item))
            y -= gap
        for y_pos, item in placed:
            style = "BubbleA" if item["speaker"] == "A" else "BubbleB"
            x = margin_x if item["speaker"] == "A" else px - margin_x
            text = "\\N".join(_escape(line) for line in _wrap(item["text"]))
            events.append(
                f"Dialogue: 0,{_ass_time(t0)},{_ass_time(t1)},{style},,0,0,0,,"
                f"{{\\pos({x},{y_pos})}}{text}\n"
            )

    header = _HEADER_TMPL.format(play_x=px, play_y=py, fontsize=fontsize, pad=pad)
    out_path.write_text(header + "".join(events), encoding="utf-8")
    return out_path, total
