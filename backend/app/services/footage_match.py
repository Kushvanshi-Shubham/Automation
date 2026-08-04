"""Auto-match: pin the creator's own footage to script scenes.

Scores each script segment's narration against the whisper transcripts of
the user's uploaded footage (plain token overlap — no LLM, no cost) and
pins the best moment (asset_id + start second) when the match is strong
enough. The renderer then cuts that clip instead of stock.
"""
import math
import re

_WORD_RE = re.compile(r"[a-z0-9']+")

# Common words that carry no matching signal.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "it", "its", "this", "that", "these",
    "those", "you", "your", "our", "we", "they", "their", "he", "she", "his", "her",
    "at", "as", "by", "from", "into", "about", "than", "then", "so", "if", "not",
    "no", "yes", "do", "does", "did", "have", "has", "had", "will", "would", "can",
    "could", "just", "here", "there", "what", "when", "how", "why", "all", "out",
    "up", "down", "now", "get", "got", "one", "two", "more", "very", "really",
}

# A pin needs at least this many shared content tokens AND this score.
MIN_SHARED_TOKENS = 3
MIN_SCORE = 0.22
# Windows of consecutive whisper chunks, capped so a pin stays one moment.
MAX_WINDOW_SECONDS = 20.0
# Two pins into the same asset must start at least this far apart.
MIN_START_SEPARATION = 3.0


def _tokens(text: str) -> set[str]:
    return {
        w for w in _WORD_RE.findall((text or "").lower())
        if len(w) >= 3 and w not in _STOPWORDS
    }


def _windows(transcript: dict) -> list[dict]:
    """Sliding windows of 1-3 consecutive transcript chunks (<= 20s each)."""
    chunks = (transcript or {}).get("segments") or []
    wins = []
    for i in range(len(chunks)):
        text_parts, start = [], float(chunks[i].get("start") or 0.0)
        for j in range(i, min(i + 3, len(chunks))):
            end = float(chunks[j].get("end") or start)
            if end - start > MAX_WINDOW_SECONDS:
                break
            text_parts.append(str(chunks[j].get("text") or ""))
            wins.append({"start": start, "tokens": _tokens(" ".join(text_parts))})
    return wins


def match_segments(segments: list[dict], footage: list[dict]) -> tuple[list[dict], int]:
    """Pin the best footage moment to each unpinned segment.

    footage: [{"id": str, "transcript": dict}]. Returns (new segments, pins).
    Segments already pinned (stock or footage) are left alone.
    """
    candidates = []
    for f in footage:
        for w in _windows(f.get("transcript") or {}):
            if w["tokens"]:
                candidates.append({"asset_id": f["id"], **w})

    used: list[tuple[str, float]] = []
    out = []
    matched = 0
    for seg in segments:
        seg = dict(seg)
        if not seg.get("asset_id") and not seg.get("media_id"):
            seg_tokens = _tokens(seg.get("text") or "")
            best, best_score = None, 0.0
            for c in candidates:
                shared = seg_tokens & c["tokens"]
                if len(shared) < MIN_SHARED_TOKENS:
                    continue
                score = len(shared) / math.sqrt(len(seg_tokens) * len(c["tokens"])) if seg_tokens else 0.0
                if score < MIN_SCORE or score <= best_score:
                    continue
                if any(
                    aid == c["asset_id"] and abs(start - c["start"]) < MIN_START_SEPARATION
                    for aid, start in used
                ):
                    continue
                best, best_score = c, score
            if best is not None:
                seg["asset_id"] = best["asset_id"]
                seg["asset_start"] = round(best["start"], 2)
                used.append((best["asset_id"], best["start"]))
                matched += 1
        out.append(seg)
    return out, matched
