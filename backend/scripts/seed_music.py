"""Seed the background-music library.

`assets/music/*.mp3` is gitignored on purpose — the repo stays lean and each
environment populates its own copy. That was fine when the library was two
files, but formats now ask for five moods, and a mood with no track silently
falls back to "any track", which is how every video ended up with the same
music.

Run from backend/:  .venv\\Scripts\\python.exe scripts\\seed_music.py

Everything here is Kevin MacLeod (incompetech.com), CC BY 4.0. The
`_kevin_macleod_ccby` suffix is load-bearing: runner._music_attribution reads
it and appends the required credit line to the video description.
"""
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/"
MUSIC_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"

# mood -> [(incompetech title, local stem)]. The local stem must contain the
# mood keyword, because runner.MOOD_KEYWORDS matches on the filename.
TRACKS: dict[str, list[tuple[str, str]]] = {
    "calm": [
        ("Wallpaper", "wallpaper_calm"),
        ("Kalimba Relaxation Music", "kalimba_calm"),
    ],
    "energetic": [
        ("Carefree", "carefree_energetic"),
        ("Wholesome", "wholesome_energetic"),
    ],
    "melancholy": [
        ("Sad Trio", "sad_trio_melancholy"),
        ("Anguish", "anguish_melancholy"),
        ("Lightless Dawn", "lightless_dawn_melancholy"),
    ],
    "tender": [
        ("Sweeter Vermouth", "sweeter_vermouth_tender"),
        ("Bittersweet", "bittersweet_tender"),
    ],
    "uplifting": [
        ("Inspired", "inspired_uplifting"),
    ],
}


def main() -> int:
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    got = skipped = failed = 0
    for mood, entries in TRACKS.items():
        for title, stem in entries:
            dest = MUSIC_DIR / f"{stem}_kevin_macleod_ccby.mp3"
            if dest.exists() and dest.stat().st_size > 100_000:
                print(f"  [skip] {mood:11} {dest.name}")
                skipped += 1
                continue
            url = BASE + urllib.parse.quote(title) + ".mp3"
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    data = r.read()
                # A 404 page is a few KB of HTML; a real track is megabytes.
                if len(data) < 100_000 or not data[:3] in (b"ID3", b"\xff\xfb\x00", b"\xff\xf3\x00"):
                    if len(data) < 100_000:
                        raise ValueError(f"suspiciously small ({len(data)} bytes) — probably a 404 page")
                dest.write_bytes(data)
                print(f"  [ok]   {mood:11} {dest.name}  ({len(data) // 1024} KB)")
                got += 1
            except Exception as exc:
                print(f"  [FAIL] {mood:11} {title}: {exc}")
                failed += 1

    print(f"\ndownloaded {got}, already present {skipped}, failed {failed}")
    print(f"library: {MUSIC_DIR}")
    return 1 if failed and not (got or skipped) else 0


if __name__ == "__main__":
    sys.exit(main())
