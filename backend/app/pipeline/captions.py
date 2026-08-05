"""Shorts-style burned-in captions (ASS subtitles) with selectable style packs.

Word-boundary events from edge-tts are grouped into short punchy cues
(2-3 words). The `karaoke` pack additionally colors each word as it is
spoken (\\k tags) — possible because we keep per-word timings.

ASS colors are &HAABBGGRR (alpha, blue, green, red).
"""
from pathlib import Path

MAX_WORDS_PER_CUE = 3

# name -> style parameters
CAPTION_STYLES: dict[str, dict] = {
    "classic": {
        "label": "Classic Bold",
        "desc": "White uppercase, black outline — the default shorts look",
        "fontsize": 88, "bold": -1, "uppercase": True, "karaoke": False,
        "primary": "&H00FFFFFF", "secondary": "&H00FFFFFF",
        "outline_colour": "&H00000000", "back_colour": "&H80000000",
        "border_style": 1, "outline": 7, "alignment": 2, "margin_v": 640,
    },
    "neon": {
        "label": "Neon Pop",
        "desc": "Electric yellow with heavy outline — high energy",
        "fontsize": 92, "bold": -1, "uppercase": True, "karaoke": False,
        "primary": "&H0000F7FF", "secondary": "&H0000F7FF",
        "outline_colour": "&H00000000", "back_colour": "&H80000000",
        "border_style": 1, "outline": 8, "alignment": 2, "margin_v": 640,
    },
    "impact": {
        "label": "Center Impact",
        "desc": "Huge center-screen text with violet outline — maximum attention",
        "fontsize": 104, "bold": -1, "uppercase": True, "karaoke": False,
        "primary": "&H00FFFFFF", "secondary": "&H00FFFFFF",
        "outline_colour": "&H00ED3A7C", "back_colour": "&H80000000",
        "border_style": 1, "outline": 8, "alignment": 5, "margin_v": 0,
    },
    "minimal": {
        "label": "Minimal Box",
        "desc": "Clean sentence-case on a soft dark box — calm & premium",
        "fontsize": 64, "bold": 0, "uppercase": False, "karaoke": False,
        "primary": "&H00FFFFFF", "secondary": "&H00FFFFFF",
        "outline_colour": "&H00000000", "back_colour": "&HA0000000",
        "border_style": 3, "outline": 10, "alignment": 2, "margin_v": 600,
    },
    "karaoke": {
        "label": "Karaoke Highlight",
        "desc": "Each word lights up yellow exactly as it's spoken",
        "fontsize": 88, "bold": -1, "uppercase": True, "karaoke": True,
        # primary = highlighted (spoken) color, secondary = not-yet-spoken color
        "primary": "&H0000F7FF", "secondary": "&H00FFFFFF",
        "outline_colour": "&H00000000", "back_colour": "&H80000000",
        "border_style": 1, "outline": 7, "alignment": 2, "margin_v": 640,
    },
}

DEFAULT_CAPTION_STYLE = "classic"

_HEADER_TMPL = """[Script Info]
ScriptType: v4.00+
PlayResX: {play_x}
PlayResY: {play_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Arial,{fontsize},{primary},{secondary},{outline_colour},{back_colour},{bold},0,0,0,100,100,1,0,{border_style},{outline},0,{alignment},60,60,{margin_v},1
Style: Mark,Arial,{mark_size},&H80FFFFFF,&H80FFFFFF,&H80000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,8,40,40,{mark_margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Free-plan mark. Burned in with the captions (same encode pass) so it
# costs nothing; Pro renders simply omit the line.
WATERMARK_TEXT = "Made with Kliptos"


def _ass_time(seconds: float) -> str:
    seconds = max(seconds, 0.0)
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def group_words(words: list[dict], max_words: int = MAX_WORDS_PER_CUE) -> list[dict]:
    """Group word events into cues of up to max_words, breaking early on
    sentence punctuation. Keeps per-word timings for karaoke styles."""
    cues: list[dict] = []
    current: list[dict] = []
    for w in words:
        current.append(w)
        ends_clause = w["word"].rstrip().endswith((".", ",", "!", "?", ";", ":"))
        if len(current) >= max_words or ends_clause:
            cues.append(_cue_from(current))
            current = []
    if current:
        cues.append(_cue_from(current))
    # Stretch each cue to meet the next so captions never flicker off.
    for i in range(len(cues) - 1):
        cues[i]["end"] = cues[i + 1]["start"]
    return cues


def _cue_from(ws: list[dict]) -> dict:
    return {
        "text": " ".join(x["word"] for x in ws),
        "start": ws[0]["start"],
        "end": ws[-1]["end"],
        "words": [dict(w) for w in ws],
    }


def fallback_cues(text: str, duration: float) -> list[dict]:
    """No word events: spread the text across the duration in 3-word chunks."""
    tokens = text.split()
    chunks = [tokens[i:i + MAX_WORDS_PER_CUE] for i in range(0, len(tokens), MAX_WORDS_PER_CUE)]
    if not chunks:
        return []
    per = duration / len(chunks)
    cues = []
    for i, chunk in enumerate(chunks):
        start, end = round(i * per, 3), round((i + 1) * per, 3)
        word_per = (end - start) / len(chunk)
        cues.append({
            "text": " ".join(chunk),
            "start": start,
            "end": end,
            "words": [
                {"word": w, "start": round(start + j * word_per, 3), "end": round(start + (j + 1) * word_per, 3)}
                for j, w in enumerate(chunk)
            ],
        })
    return cues


def _escape(text: str, uppercase: bool) -> str:
    out = text.replace("\\", "").replace("{", "(").replace("}", ")")
    return out.upper() if uppercase else out


def _karaoke_text(cue: dict, uppercase: bool) -> str:
    """Build \\k-tagged text: each word's duration in centiseconds."""
    parts = []
    for w in cue.get("words", []):
        dur_cs = max(1, round((w["end"] - w["start"]) * 100))
        parts.append(f"{{\\k{dur_cs}}}{_escape(w['word'], uppercase)}")
    return " ".join(parts) if parts else _escape(cue["text"], uppercase)


def write_ass(
    cues: list[dict],
    out_path: Path,
    style: str = DEFAULT_CAPTION_STYLE,
    play_res: tuple[int, int] = (1080, 1920),
    watermark_seconds: float | None = None,
) -> Path:
    cfg = dict(CAPTION_STYLES.get(style, CAPTION_STYLES[DEFAULT_CAPTION_STYLE]))
    # Style values are tuned for a 1920-high frame; scale to the actual
    # height so captions keep the same relative size in 1:1 / 16:9.
    s = play_res[1] / 1920
    for key in ("fontsize", "outline", "margin_v"):
        cfg[key] = max(1, round(cfg[key] * s)) if cfg[key] else cfg[key]
    cfg["mark_size"] = max(12, round(34 * s))
    cfg["mark_margin"] = max(10, round(48 * s))
    lines = [_HEADER_TMPL.format(play_x=play_res[0], play_y=play_res[1], **cfg)]
    if watermark_seconds and watermark_seconds > 0:
        lines.append(
            f"Dialogue: 1,{_ass_time(0)},{_ass_time(watermark_seconds)},Mark,,0,0,0,,{WATERMARK_TEXT}\n"
        )
    for cue in cues:
        text = _karaoke_text(cue, cfg["uppercase"]) if cfg["karaoke"] else _escape(cue["text"], cfg["uppercase"])
        lines.append(
            f"Dialogue: 0,{_ass_time(cue['start'])},{_ass_time(cue['end'])},Caption,,0,0,0,,{text}\n"
        )
    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path


def build_segment_captions(
    words: list[dict],
    text: str,
    duration: float,
    out_path: Path,
    style: str = DEFAULT_CAPTION_STYLE,
    play_res: tuple[int, int] = (1080, 1920),
    watermark: bool = False,
) -> Path:
    cues = group_words(words) if words else fallback_cues(text, duration)
    return write_ass(
        cues, out_path, style=style, play_res=play_res,
        # +0.2s so the mark never flickers out between segments
        watermark_seconds=(duration + 0.2) if watermark else None,
    )
