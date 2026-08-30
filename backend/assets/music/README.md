# Background music library

Drop `.mp3` files here — the pipeline picks one at random per render and mixes
it under the narration at 12% volume. If the folder is empty, renders simply
have no music.

These `.mp3` files ARE tracked in git, via a deliberate negation in
`.gitignore` (`!backend/assets/music/*.mp3`). They have to be: Render builds
from the repo, and when they were ignored every cloud render came out silent.

Keep them small. They are mixed at 12% under narration, so mono 96 kbps is
indistinguishable from stereo 256 kbps and one fifth the size:
`ffmpeg -i in.mp3 -ac 1 -b:a 96k out.mp3`

## Licensing rules

Only add tracks you have rights to. Naming convention for attribution-required
tracks: `<title>_kevin_macleod_ccby.mp3` — the pipeline auto-appends the
CC-BY attribution line to the video description when such a track is used.

Run `.venv\Scripts\python.exe scripts\seed_music.py` to populate this folder.
It is idempotent and skips anything already present.

## Moods

`runner.MOOD_KEYWORDS` matches on the FILENAME, so a track's stem must contain
its mood keyword or it will never be picked for that mood. A mood with no
matching track falls back to the whole library and logs a warning — that
fallback is why every video used to get the same music.

| mood | tracks |
|---|---|
| calm | wallpaper, kalimba |
| energetic | carefree, wholesome |
| melancholy | sad_trio, anguish, lightless_dawn |
| tender | sweeter_vermouth, bittersweet |
| uplifting | inspired |

Seeded 2026-08-30 (10 tracks, all Kevin MacLeod / incompetech.com, CC BY 4.0).
