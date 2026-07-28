# Background music library

Drop `.mp3` files here — the pipeline picks one at random per render and mixes
it under the narration at 12% volume. If the folder is empty, renders simply
have no music.

`.mp3` files are gitignored (repo stays lean); each environment seeds its own
library. In production this folder is replaced by object storage.

## Licensing rules

Only add tracks you have rights to. Naming convention for attribution-required
tracks: `<title>_kevin_macleod_ccby.mp3` — the pipeline auto-appends the
CC-BY attribution line to the video description when such a track is used.

Current dev tracks (downloaded 2026-07-29):
- `carefree_kevin_macleod_ccby.mp3` — "Carefree" Kevin MacLeod (incompetech.com), CC BY 4.0
- `wallpaper_kevin_macleod_ccby.mp3` — "Wallpaper" Kevin MacLeod (incompetech.com), CC BY 4.0
