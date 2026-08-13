"""Caption craft layer: animations, fonts, brand colour, headline overlays."""
from pathlib import Path

from app.pipeline import captions
from app.pipeline.captions import (
    CAPTION_ANIMATIONS,
    CAPTION_FONTS,
    DEFAULT_CAPTION_ANIMATION,
    DEFAULT_CAPTION_FONT,
    build_segment_captions,
    hex_to_ass,
    write_ass,
)

WORDS = [
    {"word": "The", "start": 0.1, "end": 0.27},
    {"word": "ocean", "start": 0.29, "end": 0.70},
    {"word": "covers", "start": 0.71, "end": 1.07},
    {"word": "seventy", "start": 1.09, "end": 1.43},
    {"word": "percent,", "start": 1.44, "end": 1.83},
    {"word": "easily.", "start": 1.9, "end": 2.4},
]

BRAND = "#7C3AED"
BRAND_ASS = "&H00ED3A7C"


def _dialogues(text: str, style: str | None = None) -> list[str]:
    out = [ln for ln in text.splitlines() if ln.startswith("Dialogue:")]
    if style:
        out = [ln for ln in out if ln.split(",")[3] == style]
    return out


def _dialogue_text(line: str) -> str:
    return line.split(",", 9)[9]


def _style_fields(text: str, name: str) -> list[str]:
    for ln in text.splitlines():
        if ln.startswith(f"Style: {name},"):
            return ln[len("Style: "):].split(",")
    raise AssertionError(f"no Style: {name} line in\n{text}")


def _render(tmp_path: Path, name: str, **kwargs) -> str:
    out = build_segment_captions(WORDS, "x", 2.5, tmp_path / f"{name}.ass", **kwargs)
    return out.read_text(encoding="utf-8")


# --- registries -------------------------------------------------------------

def test_registries_expose_labels_and_defaults():
    assert set(CAPTION_ANIMATIONS) == {"none", "fade", "pop", "highlight", "typewriter"}
    assert all({"label", "desc"} <= set(v) for v in CAPTION_ANIMATIONS.values())
    assert DEFAULT_CAPTION_ANIMATION in CAPTION_ANIMATIONS

    assert set(CAPTION_FONTS) == {"arial", "impact", "verdana", "georgia", "dejavu", "liberation"}
    assert all({"label", "family"} <= set(v) for v in CAPTION_FONTS.values())
    assert DEFAULT_CAPTION_FONT in CAPTION_FONTS
    assert CAPTION_FONTS[DEFAULT_CAPTION_FONT]["family"] == "Arial"


# --- animations -------------------------------------------------------------

def test_every_animation_renders_a_parseable_file(tmp_path: Path):
    for anim in CAPTION_ANIMATIONS:
        text = _render(tmp_path, f"anim_{anim}", animation=anim)
        assert "[Script Info]" in text and "[V4+ Styles]" in text and "[Events]" in text
        assert "Style: Caption," in text
        assert _dialogues(text, "Caption"), anim


def test_fade_animation_tag(tmp_path: Path):
    text = _render(tmp_path, "fade", animation="fade")
    assert all(_dialogue_text(ln).startswith("{\\fad(120,120)}") for ln in _dialogues(text, "Caption"))


def test_pop_animation_scales_in(tmp_path: Path):
    text = _render(tmp_path, "pop", animation="pop")
    lines = _dialogues(text, "Caption")
    assert lines
    for ln in lines:
        body = _dialogue_text(ln)
        assert body.startswith("{\\fscx80\\fscy80\\t(0,120,\\fscx100\\fscy100)}")
    assert "\\fscy" in text


def test_highlight_animation_forces_karaoke(tmp_path: Path):
    # classic pack has karaoke=False, but the animation must still emit \k tags
    text = _render(tmp_path, "hl", style="classic", animation="highlight")
    assert "{\\k" in text
    per_word = [t for t in _dialogue_text(_dialogues(text, "Caption")[0]).split() if t.startswith("{\\k")]
    assert len(per_word) == 3  # "The ocean covers"


def test_typewriter_emits_one_line_per_word(tmp_path: Path):
    plain = _render(tmp_path, "tw_plain")
    typed = _render(tmp_path, "tw", animation="typewriter")
    plain_cues = _dialogues(plain, "Caption")
    typed_cues = _dialogues(typed, "Caption")
    assert len(typed_cues) > len(plain_cues)
    assert len(typed_cues) == len(WORDS)  # 3 + 2 + 1 words across three cues
    # first cue builds up progressively
    assert _dialogue_text(typed_cues[0]) == "THE"
    assert _dialogue_text(typed_cues[1]) == "THE OCEAN"
    assert _dialogue_text(typed_cues[2]) == "THE OCEAN COVERS"
    # Each stage starts on its own word and HANDS OVER to the next one.
    # (It must not run to the cue end — that stacks every prefix on screen,
    # which is what a real render showed before this was fixed.)
    assert typed_cues[1].startswith("Dialogue: 0,0:00:00.29,")
    assert typed_cues[0].split(",")[2] == "0:00:00.29", "step 1 ends where word 2 starts"
    assert typed_cues[1].split(",")[2] == "0:00:00.71", "step 2 ends where word 3 starts"
    # Only the final step of a cue holds until the cue ends.
    assert typed_cues[2].split(",")[2] > typed_cues[1].split(",")[2]


def test_typewriter_without_word_timings_falls_back(tmp_path: Path):
    cues = [{"text": "no timings here", "start": 0.0, "end": 2.0}]
    text = write_ass(cues, tmp_path / "tw0.ass", animation="typewriter").read_text(encoding="utf-8")
    assert len(_dialogues(text, "Caption")) == 1
    assert "NO TIMINGS HERE" in text


# --- silent fallbacks -------------------------------------------------------

def test_unknown_animation_font_and_colour_fall_back_silently(tmp_path: Path):
    text = _render(tmp_path, "junk", animation="disco", font="comic-papyrus", color="nope")
    assert "Style: Caption,Arial,88," in text          # default font kept
    assert _style_fields(text, "Caption")[3] == "&H00FFFFFF"  # classic primary kept
    assert "\\fad" not in text and "\\fscx" not in text and "{\\k" not in text
    assert len(_dialogues(text, "Caption")) == 3       # behaves like "none"


def test_hex_to_ass_conversions():
    assert hex_to_ass("#7C3AED") == BRAND_ASS
    assert hex_to_ass("7c3aed") == BRAND_ASS           # no hash, lowercase
    assert hex_to_ass("  #7C3AED  ") == BRAND_ASS
    assert hex_to_ass("#fff") == "&H00FFFFFF"          # short form expands
    assert hex_to_ass("#000000") == "&H00000000"
    assert hex_to_ass("nope") is None
    assert hex_to_ass("#12345") is None
    assert hex_to_ass("#GGHHII") is None
    assert hex_to_ass("") is None
    assert hex_to_ass(None) is None
    assert hex_to_ass(123) is None


# --- fonts ------------------------------------------------------------------

def test_font_key_changes_the_caption_fontname(tmp_path: Path):
    text = _render(tmp_path, "font", font="dejavu")
    caption = _style_fields(text, "Caption")
    assert caption[1] == "DejaVu Sans"
    # the watermark style is deliberately left on Arial
    assert _style_fields(text, "Mark")[1] == "Arial"

    impact = _style_fields(_render(tmp_path, "font2", font="impact"), "Caption")
    assert impact[1] == "Impact"


# --- brand colour -----------------------------------------------------------

def test_brand_colour_is_primary_for_pop_and_secondary_for_highlight(tmp_path: Path):
    pop = _style_fields(_render(tmp_path, "cpop", animation="pop", color=BRAND), "Caption")
    assert pop[3] == BRAND_ASS            # PrimaryColour = text fill
    assert pop[4] == "&H00FFFFFF"         # SecondaryColour untouched
    assert pop[5] == "&H00000000"         # outline still from the style pack

    hl = _style_fields(_render(tmp_path, "chl", animation="highlight", color=BRAND), "Caption")
    assert hl[4] == BRAND_ASS             # SecondaryColour = the highlight
    assert hl[3] == "&H00FFFFFF"          # fill untouched

    # "none" also tints the fill
    plain = _style_fields(_render(tmp_path, "cnone", color="7c3aed"), "Caption")
    assert plain[3] == BRAND_ASS


# --- headline overlays ------------------------------------------------------

def test_headline_appears_once_on_its_own_style_with_a_fade(tmp_path: Path):
    text = _render(tmp_path, "head", headline="Why the ocean matters")
    heads = _dialogues(text, "Headline")
    assert len(heads) == 1
    assert heads[0].startswith("Dialogue: 2,0:00:00.00,0:00:02.70,Headline,")  # duration + 0.2
    assert _dialogue_text(heads[0]) == "{\\fad(200,200)}Why the ocean matters"
    head_style = _style_fields(text, "Headline")
    assert head_style[15] == "3"    # BorderStyle 3 = box behind the text
    assert head_style[6].startswith("&HA0")  # semi-transparent BackColour
    assert head_style[7] == "-1"    # bold
    assert int(head_style[18]) == 8  # Alignment 8 = top-centre
    # bigger than the minimal pack's copy; capped so 28 chars still fit 1080 wide
    assert int(head_style[2]) == captions.HEADLINE_FONTSIZE
    assert int(head_style[2]) > int(_style_fields(text, "Mark")[2])


def test_headline_is_capped_and_wrapped_to_two_lines(tmp_path: Path):
    long = ("The complete guide to shipping a production video pipeline "
            "without ever losing your mind again")
    assert len(long) > 90
    text = _render(tmp_path, "long", headline=long)
    body = _dialogue_text(_dialogues(text, "Headline")[0]).replace("{\\fad(200,200)}", "")
    parts = body.split("\\N")
    assert len(parts) <= 2
    assert all(len(p) <= 32 for p in parts), parts
    assert len("".join(parts)) <= 92  # 90-char cap (+ ellipsis)
    assert body.endswith("…")


def test_headline_keeps_its_own_case_and_survives_braces(tmp_path: Path):
    text = _render(tmp_path, "case", headline="Mixed Case {stays}")
    body = _dialogue_text(_dialogues(text, "Headline")[0])
    assert "Mixed Case" in body and "MIXED CASE" not in body
    assert "(stays)" in body  # braces neutralised so libass can't parse them


def test_headline_and_watermark_coexist_without_colliding(tmp_path: Path):
    text = _render(tmp_path, "both", headline="Chapter one", watermark=True)
    assert captions.WATERMARK_TEXT in text
    assert len(_dialogues(text, "Headline")) == 1
    assert len(_dialogues(text, "Mark")) == 1
    mark, head = _style_fields(text, "Mark"), _style_fields(text, "Headline")
    # both are Alignment 8 (top-centre): the headline must clear the mark's box
    assert int(mark[18]) == 8 and int(head[18]) == 8
    assert int(head[21]) > int(mark[21]) + int(mark[2]) * 1.2


def test_headline_seconds_defaults_to_the_last_cue_when_unset(tmp_path: Path):
    cues = [{"text": "a b", "start": 0.0, "end": 5.0,
             "words": [{"word": "a", "start": 0.0, "end": 2.5},
                       {"word": "b", "start": 2.5, "end": 5.0}]}]
    text = write_ass(cues, tmp_path / "hs.ass", headline="Title").read_text(encoding="utf-8")
    assert _dialogues(text, "Headline")[0].startswith("Dialogue: 2,0:00:00.00,0:00:05.00,")

    empty = write_ass([], tmp_path / "hs0.ass", headline="Title").read_text(encoding="utf-8")
    assert _dialogues(empty, "Headline")[0].startswith("Dialogue: 2,0:00:00.00,0:00:04.00,")


# --- backwards compatibility ------------------------------------------------

def test_omitting_new_params_matches_the_old_behaviour(tmp_path: Path):
    old = _render(tmp_path, "old")
    assert len(_dialogues(old, "Caption")) == 3
    assert "Style: Caption,Arial,88," in old
    assert "Style: Headline" not in old
    assert "\\fad" not in old and "\\fscx" not in old and "{\\k" not in old
    assert "THE OCEAN COVERS" in old
    assert old.startswith("[Script Info]\nScriptType: v4.00+\n")
    # the blank line before [Events] is preserved even with no Headline style
    assert "{mark_margin},1\n" not in old and ",1\n\n[Events]\n" in old

    # the clip branch's positional call keeps working
    clip = write_ass(
        captions.group_words(WORDS), tmp_path / "clip.ass",
        style="neon", play_res=(1920, 1080), watermark_seconds=3.2,
    ).read_text(encoding="utf-8")
    assert "PlayResX: 1920" in clip and captions.WATERMARK_TEXT in clip
    assert "&H0000F7FF" in clip and "Style: Headline" not in clip


def test_new_params_compose_with_style_packs_and_aspect(tmp_path: Path):
    out = write_ass(
        captions.group_words(WORDS), tmp_path / "combo.ass",
        style="minimal", play_res=(1920, 1080), watermark_seconds=3.2,
        animation="fade", font="liberation", color="#7C3AED",
        headline="Scene one", headline_seconds=3.2,
    ).read_text(encoding="utf-8")
    caption = _style_fields(out, "Caption")
    assert caption[1] == "Liberation Sans"
    assert caption[3] == BRAND_ASS
    assert caption[2] == "36"                       # 64 scaled to a 1080-high frame
    assert _style_fields(out, "Headline")[2] == "40"  # 72 * 1080/1920
    assert "The ocean covers" in out                # minimal keeps sentence case
    assert len(_dialogues(out, "Headline")) == 1
    assert captions.WATERMARK_TEXT in out


def _seconds(stamp: str) -> float:
    """'0:00:01.44' -> 1.44"""
    h, m, s = stamp.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _spans(text: str, style: str = "Caption") -> list[tuple[float, float, str]]:
    spans = []
    for ln in _dialogues(text, style):
        parts = ln.split(",", 9)
        spans.append((_seconds(parts[1]), _seconds(parts[2]), parts[9]))
    return sorted(spans)


def test_no_animation_ever_puts_two_captions_on_screen_at_once(tmp_path):
    """Overlapping cues get stacked vertically by libass — the same words
    appear two or three times up the frame. Caught in a real render: the
    typewriter build-up held every prefix until the end of the cue."""
    for anim in CAPTION_ANIMATIONS:
        text = _render(tmp_path, f"overlap_{anim}", animation=anim)
        spans = _spans(text)
        assert spans, f"{anim} produced no caption lines"
        for (a_start, a_end, a_text), (b_start, b_end, _) in zip(spans, spans[1:]):
            assert a_end <= b_start + 1e-6, (
                f"{anim}: '{a_text}' runs to {a_end} but the next caption starts "
                f"at {b_start} — they would stack on screen"
            )


def test_typewriter_builds_each_cue_up_word_by_word(tmp_path):
    """WORDS groups into several cues (punctuation breaks them), so the
    build-up restarts per cue. Within a cue each step must extend the one
    before it — never repeat or reorder."""
    spans = _spans(_render(tmp_path, "tw_order", animation="typewriter"))
    previous = ""
    for _, _, current in spans:
        words = current.split()
        if len(words) == 1:
            previous = current  # a new cue starts its own build-up
            continue
        assert current.startswith(previous), f"'{current}' does not extend '{previous}'"
        previous = current
