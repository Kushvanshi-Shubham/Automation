"""Shorts-style burned-in captions (ASS subtitles) with selectable style packs.

Word-boundary events from edge-tts are grouped into short punchy cues
(2-3 words). The `karaoke` pack additionally colors each word as it is
spoken (\\k tags) — possible because we keep per-word timings.

On top of the style packs, the "caption craft" layer adds:
  * animations (CAPTION_ANIMATIONS) — libass override tags on the Dialogue lines
  * a font choice (CAPTION_FONTS) — swaps the Caption style's Fontname
  * a brand colour (hex -> ASS BGR) — the text fill, or the highlight colour
  * per-scene headline overlays — an upper-third title card on its own style

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

# name -> animation metadata. The tags themselves live in _ANIMATION_PREFIX
# (typewriter is structural: it emits several Dialogue lines per cue).
CAPTION_ANIMATIONS: dict[str, dict] = {
    "none": {"label": "Static", "desc": "Cues cut straight in and out — the default shorts look"},
    "fade": {"label": "Fade", "desc": "Every cue eases in and out — calm, premium feel"},
    "pop": {"label": "Pop", "desc": "Cues snap in with a quick scale overshoot — punchy"},
    "highlight": {"label": "Word highlight", "desc": "Each word changes colour exactly as it is spoken"},
    "typewriter": {"label": "Typewriter", "desc": "Words appear one at a time, in time with the voice"},
}

DEFAULT_CAPTION_ANIMATION = "none"

# ASS override prefixes, applied to the start of each cue's Text field.
_ANIMATION_PREFIX: dict[str, str] = {
    "none": "",
    "fade": r"{\fad(120,120)}",
    "pop": r"{\fscx80\fscy80\t(0,120,\fscx100\fscy100)}",
    # highlight rides the \k karaoke mechanism, typewriter emits extra lines
    "highlight": "",
    "typewriter": "",
}

# key -> font. Families must exist in the render image; DejaVu/Liberation
# ship with our Docker base, the rest are there for local/Windows renders.
CAPTION_FONTS: dict[str, dict] = {
    "arial": {"label": "Arial", "family": "Arial"},
    "impact": {"label": "Impact", "family": "Impact"},
    "verdana": {"label": "Verdana", "family": "Verdana"},
    "georgia": {"label": "Georgia", "family": "Georgia"},
    "dejavu": {"label": "DejaVu Sans", "family": "DejaVu Sans"},
    "liberation": {"label": "Liberation Sans", "family": "Liberation Sans"},
}

DEFAULT_CAPTION_FONT = "arial"

# Fallback highlight tint when animation="highlight" runs on a style pack that
# isn't karaoke and no brand colour was supplied (white-on-white = no effect).
HIGHLIGHT_FALLBACK_COLOUR = "&H0000F7FF"

# Headline overlay geometry, tuned for a 1920-high frame (scaled like the rest).
HEADLINE_FONTSIZE = 72
HEADLINE_BOX_PAD = 12
HEADLINE_MARGIN_V = 200      # from the top (Alignment 8); clears the Mark
HEADLINE_MAX_CHARS = 90
HEADLINE_WRAP_CHARS = 28
HEADLINE_MAX_LINES = 2

_HEADER_TMPL = """[Script Info]
ScriptType: v4.00+
PlayResX: {play_x}
PlayResY: {play_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{fontname},{fontsize},{primary},{secondary},{outline_colour},{back_colour},{bold},0,0,0,100,100,1,0,{border_style},{outline},0,{alignment},60,60,{margin_v},1
Style: Mark,Arial,{mark_size},&H80FFFFFF,&H80FFFFFF,&H80000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,8,40,40,{mark_margin},1
{headline_style}
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

# Only emitted when a headline is actually requested, so files without one stay
# byte-identical to the pre-headline output. Alignment 8 = top-centre,
# BorderStyle 3 = opaque box (drawn from OutlineColour, shadowed with BackColour).
_HEADLINE_STYLE_TMPL = (
    "Style: Headline,{headline_font},{headline_size},&H00FFFFFF,&H00FFFFFF,"
    "&HA0101010,&HA0000000,-1,0,0,0,100,100,0,0,3,{headline_pad},0,8,60,60,{headline_margin},1\n"
)

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


def hex_to_ass(hex_str: str | None) -> str | None:
    """'#7C3AED' -> '&H00ED3A7C' (ASS is &HAABBGGRR). None on anything odd —
    a bad brand colour must never break a render."""
    if not isinstance(hex_str, str):
        return None
    h = hex_str.strip().lstrip("#").strip()
    if len(h) == 3:  # #abc -> #aabbcc
        h = "".join(c * 2 for c in h)
    if len(h) == 8:  # #rrggbbaa -> drop the alpha, we always render opaque
        h = h[:6]
    if len(h) != 6:
        return None
    try:
        int(h, 16)
    except ValueError:
        return None
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}".upper()


def _wrap_headline(text: str) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > HEADLINE_WRAP_CHARS:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > HEADLINE_MAX_LINES:
        lines = lines[:HEADLINE_MAX_LINES]
        lines[-1] = lines[-1] + "…"
    return lines or [""]


def headline_text(raw: str) -> str:
    """Capped, wrapped, escaped headline ready for an ASS Text field."""
    flat = " ".join(str(raw).split())[:HEADLINE_MAX_CHARS]
    return "\\N".join(_escape(line, uppercase=False) for line in _wrap_headline(flat))


def _cue_text(cue: dict, uppercase: bool, karaoke: bool) -> str:
    return _karaoke_text(cue, uppercase) if karaoke else _escape(cue["text"], uppercase)


def _dialogue(start: float, end: float, style: str, text: str, layer: int = 0) -> str:
    return f"Dialogue: {layer},{_ass_time(start)},{_ass_time(end)},{style},,0,0,0,,{text}\n"


def _typewriter_lines(cue: dict, uppercase: bool, prefix: str) -> list[str]:
    """One Dialogue line per word prefix, so the cue builds up word by word.

    Each prefix must END where the next word begins — if every line ran to
    the end of the cue they would all be on screen together and libass
    would stack them, showing the same words several times over.

    Falls back to the plain cue when the cue carries no word timings.
    """
    words = cue.get("words") or []
    if not words:
        return []
    out = []
    for k in range(1, len(words) + 1):
        shown = " ".join(w["word"] for w in words[:k])
        start = words[k - 1]["start"]
        # Last prefix holds until the cue ends; the others hand over to the
        # next word so exactly one line is ever visible.
        end = cue["end"] if k == len(words) else words[k]["start"]
        if end <= start:  # zero-length word events would flicker
            continue
        out.append(_dialogue(start, end, "Caption", f"{prefix}{_escape(shown, uppercase)}"))
    return out


def write_ass(
    cues: list[dict],
    out_path: Path,
    style: str = DEFAULT_CAPTION_STYLE,
    play_res: tuple[int, int] = (1080, 1920),
    watermark_seconds: float | None = None,
    animation: str = "none",
    font: str | None = None,
    color: str | None = None,
    headline: str | None = None,
    headline_seconds: float | None = None,
) -> Path:
    cfg = dict(CAPTION_STYLES.get(style, CAPTION_STYLES[DEFAULT_CAPTION_STYLE]))
    anim = animation if animation in CAPTION_ANIMATIONS else DEFAULT_CAPTION_ANIMATION
    cfg["fontname"] = CAPTION_FONTS.get(font or "", CAPTION_FONTS[DEFAULT_CAPTION_FONT])["family"]

    # Brand colour: the text fill, except for "highlight" where it is the
    # colour a word turns into as it is spoken (ASS SecondaryColour).
    brand = hex_to_ass(color)
    if anim == "highlight":
        if brand:
            cfg["secondary"] = brand
        elif not cfg["karaoke"]:
            cfg["secondary"] = HIGHLIGHT_FALLBACK_COLOUR
    elif brand:
        cfg["primary"] = brand
    karaoke = bool(cfg["karaoke"]) or anim == "highlight"

    # Style values are tuned for a 1920-high frame; scale to the actual
    # height so captions keep the same relative size in 1:1 / 16:9.
    s = play_res[1] / 1920
    for key in ("fontsize", "outline", "margin_v"):
        cfg[key] = max(1, round(cfg[key] * s)) if cfg[key] else cfg[key]
    cfg["mark_size"] = max(12, round(34 * s))
    cfg["mark_margin"] = max(10, round(48 * s))

    head = str(headline).strip() if headline else ""
    cfg["headline_style"] = _HEADLINE_STYLE_TMPL.format(
        headline_font=cfg["fontname"],
        headline_size=max(16, round(HEADLINE_FONTSIZE * s)),
        headline_pad=max(4, round(HEADLINE_BOX_PAD * s)),
        # sits well below the Mark (top-centre, ~48+34 scaled) — no collision
        headline_margin=max(24, round(HEADLINE_MARGIN_V * s)),
    ) if head else ""

    lines = [_HEADER_TMPL.format(play_x=play_res[0], play_y=play_res[1], **cfg)]
    if watermark_seconds and watermark_seconds > 0:
        lines.append(
            f"Dialogue: 1,{_ass_time(0)},{_ass_time(watermark_seconds)},Mark,,0,0,0,,{WATERMARK_TEXT}\n"
        )
    if head:
        until = headline_seconds if headline_seconds and headline_seconds > 0 else None
        if until is None:
            until = max((c["end"] for c in cues), default=0.0) or 4.0
        lines.append(_dialogue(
            0.0, until, "Headline", f"{{\\fad(200,200)}}{headline_text(head)}", layer=2,
        ))

    prefix = _ANIMATION_PREFIX.get(anim, "")
    for cue in cues:
        typed = _typewriter_lines(cue, cfg["uppercase"], prefix) if anim == "typewriter" else []
        if typed:
            lines.extend(typed)
        else:
            lines.append(_dialogue(
                cue["start"], cue["end"], "Caption",
                f"{prefix}{_cue_text(cue, cfg['uppercase'], karaoke)}",
            ))
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
    animation: str = "none",
    font: str | None = None,
    color: str | None = None,
    headline: str | None = None,
) -> Path:
    cues = group_words(words) if words else fallback_cues(text, duration)
    return write_ass(
        cues, out_path, style=style, play_res=play_res,
        # +0.2s so the mark never flickers out between segments
        watermark_seconds=(duration + 0.2) if watermark else None,
        animation=animation, font=font, color=color, headline=headline,
        headline_seconds=(duration + 0.2) if headline else None,
    )
