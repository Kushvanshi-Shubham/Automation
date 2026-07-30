"""Shorts-style burned-in captions (ASS subtitles).

Word-boundary events from edge-tts are grouped into short punchy cues
(2-3 words), styled bold-white-with-outline in the lower-middle of the
9:16 frame — the format viewers expect from Shorts/Reels.
"""
from pathlib import Path

MAX_WORDS_PER_CUE = 3

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,7,0,2,60,60,640,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_time(seconds: float) -> str:
    seconds = max(seconds, 0.0)
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def group_words(words: list[dict], max_words: int = MAX_WORDS_PER_CUE) -> list[dict]:
    """Group word events into cues of up to max_words, breaking early on
    sentence punctuation so cues follow the phrasing."""
    cues: list[dict] = []
    current: list[dict] = []
    for w in words:
        current.append(w)
        ends_clause = w["word"].rstrip().endswith((".", ",", "!", "?", ";", ":"))
        if len(current) >= max_words or ends_clause:
            cues.append(
                {
                    "text": " ".join(x["word"] for x in current),
                    "start": current[0]["start"],
                    "end": current[-1]["end"],
                }
            )
            current = []
    if current:
        cues.append(
            {
                "text": " ".join(x["word"] for x in current),
                "start": current[0]["start"],
                "end": current[-1]["end"],
            }
        )
    # Stretch each cue to meet the next so captions never flicker off.
    for i in range(len(cues) - 1):
        cues[i]["end"] = cues[i + 1]["start"]
    return cues


def fallback_cues(text: str, duration: float) -> list[dict]:
    """No word events: spread the text across the duration in 3-word chunks."""
    tokens = text.split()
    chunks = [" ".join(tokens[i:i + MAX_WORDS_PER_CUE]) for i in range(0, len(tokens), MAX_WORDS_PER_CUE)]
    if not chunks:
        return []
    per = duration / len(chunks)
    return [
        {"text": c, "start": round(i * per, 3), "end": round((i + 1) * per, 3)}
        for i, c in enumerate(chunks)
    ]


def _escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")").upper()


def write_ass(cues: list[dict], out_path: Path) -> Path:
    lines = [ASS_HEADER]
    for cue in cues:
        lines.append(
            f"Dialogue: 0,{_ass_time(cue['start'])},{_ass_time(cue['end'])},Caption,,0,0,0,,{_escape(cue['text'])}\n"
        )
    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path


def build_segment_captions(
    words: list[dict],
    text: str,
    duration: float,
    out_path: Path,
) -> Path:
    cues = group_words(words) if words else fallback_cues(text, duration)
    return write_ass(cues, out_path)
