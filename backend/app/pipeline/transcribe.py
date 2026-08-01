"""Transcription (faster-whisper, local, word timestamps) + highlight mining."""
import json
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger("kliptos.transcribe")

WHISPER_MODEL = "base"  # ~150MB, good speed/quality tradeoff for clips
_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        logger.info("loading whisper model '%s'…", WHISPER_MODEL)
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def extract_audio(source: Path, out_wav: Path) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", str(out_wav)],
        capture_output=True, text=True, timeout=1800,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"audio extraction failed: {proc.stderr[-300:]}")


def transcribe(source: Path) -> dict:
    """Whisper transcript with segment + word timestamps."""
    with tempfile.TemporaryDirectory(prefix="kliptos_asr_") as tmp:
        wav = Path(tmp) / "audio.wav"
        extract_audio(source, wav)
        segments_iter, info = _get_model().transcribe(str(wav), word_timestamps=True)
        segments = []
        for seg in segments_iter:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "words": [
                    {"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)}
                    for w in (seg.words or [])
                ],
            })
    return {"language": info.language, "segments": segments}


def words_in_range(transcript: dict, start: float, end: float) -> list[dict]:
    """Word events overlapping [start, end], times shifted so the clip
    starts at 0 — ready for the caption builder."""
    out = []
    for seg in transcript.get("segments", []):
        if seg["end"] < start or seg["start"] > end:
            continue
        for w in seg.get("words", []):
            if w["end"] <= start or w["start"] >= end:
                continue
            out.append({
                "word": w["word"],
                "start": round(max(w["start"] - start, 0.0), 3),
                "end": round(min(w["end"], end) - start, 3),
            })
    return out


HIGHLIGHT_SYSTEM = (
    "You are a short-form clip producer. Given a timestamped transcript of a long video, pick the "
    "3-6 BEST self-contained moments to publish as vertical clips (15-60 seconds each). Prefer: "
    "strong hooks, complete thoughts, emotional or surprising moments, actionable insights. Clips "
    "must start at a natural sentence beginning and end at a natural stop.\n"
    'Respond ONLY with JSON: {"highlights": [{"start": 12.5, "end": 48.0, '
    '"title": "clip title under 90 chars", "reason": "why this works, under 12 words"}]}'
)


async def suggest_highlights(transcript: dict, user_keys: dict | None = None) -> list[dict]:
    from app.services.llm import generate_json

    lines = [
        f"[{s['start']:.0f}s–{s['end']:.0f}s] {s['text']}"
        for s in transcript.get("segments", [])
    ]
    text = "\n".join(lines)[:24000]
    data = await generate_json(HIGHLIGHT_SYSTEM, f"Transcript:\n{text}\n\nPick the best clips.",
                               temperature=0.4, user_keys=user_keys)
    out = []
    for h in data.get("highlights", [])[:8]:
        try:
            start, end = float(h["start"]), float(h["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if end - start < 5 or end - start > 90:
            continue
        out.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "title": str(h.get("title", ""))[:90],
            "reason": str(h.get("reason", ""))[:120],
        })
    return out
