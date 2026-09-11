"""FFmpeg-based video assembly.

Direct ffmpeg subprocess calls instead of MoviePy: fewer heavy dependencies
(numpy/imageio), faster renders, and the exact filters we need.

Per segment: loop/trim the clip to the narration length, scale+crop to
1080x1920@30fps, mux with the segment audio. Then concat all segments with
stream copy (identical codecs).
"""
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("kliptos.assembler")

# Output aspect ratios. w/h drive the ffmpeg crop and the ASS caption
# resolution; orientation drives Pexels search so footage fits the frame.
ASPECT_RATIOS: dict[str, dict] = {
    "9:16": {"w": 1080, "h": 1920, "orientation": "portrait", "label": "Vertical", "desc": "Shorts · Reels · TikTok"},
    "1:1": {"w": 1080, "h": 1080, "orientation": "square", "label": "Square", "desc": "Feed posts"},
    "16:9": {"w": 1920, "h": 1080, "orientation": "landscape", "label": "Widescreen", "desc": "YouTube · X"},
}
DEFAULT_ASPECT = "9:16"


# Ken Burns speeds, as (zoom-per-frame, ceiling). formats.MOTIONS holds the
# human labels for the same keys; test_editing_grammar keeps the two in step. A shot that moves at news
# speed under a couplet feels restless; one that barely moves under a news
# update feels dead. Same filter, four intents.
MOTION_CURVES: dict[str, tuple[float, float]] = {
    "kenburns": (0.0009, 1.18),   # the original default - do not change
    "drift":    (0.00025, 1.06),  # ~6% over a 7s shot: felt, not seen
    "punch":    (0.0025, 1.25),
    "still":    (0.0, 1.0),
}


def _fade_filter(duration: float, fade: float) -> str:
    """Fade the composed frame in and out. Applied last, so captions fade
    with the picture instead of popping onto a black frame."""
    if fade <= 0 or duration <= fade * 2:
        return ""
    out_start = max(0.0, duration - fade)
    return f",fade=t=in:st=0:d={fade:.2f},fade=t=out:st={out_start:.2f}:d={fade:.2f}"


def _vf(width: int, height: int) -> str:
    return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30,format=yuv420p"


VF = _vf(1080, 1920)  # legacy default (9:16)


def _run(args: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(cwd) if cwd else None,
    )
    if proc.returncode != 0:
        logger.error("ffmpeg failed: %s", proc.stderr[-2000:])
        raise RuntimeError(f"ffmpeg failed: {proc.stderr[-500:]}")


def render_segment(
    clip_path: Path,
    audio_path: Path,
    duration: float,
    out_path: Path,
    ass_path: Path | None = None,
    width: int = 1080,
    height: int = 1920,
    fade: float = 0.0,
) -> None:
    """Video looped/trimmed to narration duration, cropped to the target
    aspect, with segment audio and optional burned-in captions.

    `fade` softens both edges of the shot. It is a per-segment effect rather
    than a true cross-dissolve on purpose: an xfade chain shortens the video
    by (n-1)*d while the narration keeps its full length, and nothing in this
    pipeline would re-sync them. This costs no duration and cannot desync.
    """
    vf = _vf(width, height)
    if ass_path is not None:
        # Run with cwd = the ASS file's directory and reference it by bare
        # filename — sidesteps Windows drive-letter escaping in filter args.
        vf = f"{vf},ass={ass_path.name}:fontsdir=."
    vf += _fade_filter(duration + 0.15, fade)
    _run(
        [
            "-stream_loop", "-1",
            "-i", str(clip_path),
            "-i", str(audio_path),
            "-t", f"{duration + 0.15:.2f}",  # small tail so audio never clips
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            str(out_path),
        ],
        cwd=ass_path.parent if ass_path is not None else None,
    )


def render_segment_silent(
    clip_path: Path,
    duration: float,
    out_path: Path,
    ass_path: Path | None = None,
    width: int = 1080,
    height: int = 1920,
    fade: float = 0.0,
) -> None:
    """Visual-only segment: no narration track (music is added after concat)."""
    vf = _vf(width, height)
    if ass_path is not None:
        vf = f"{vf},ass={ass_path.name}:fontsdir=."
    vf += _fade_filter(duration, fade)
    _run(
        [
            "-stream_loop", "-1",
            "-i", str(clip_path),
            "-t", f"{duration:.2f}",
            "-vf", vf,
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            str(out_path),
        ],
        cwd=ass_path.parent if ass_path is not None else None,
    )


# Broadcast-style target. Measured across 18 real renders, output loudness
# spanned 14.6 dB (-12.6 to -27.2 LUFS) — a real channel sits inside about 1 dB,
# and a viewer reaches for the volume slider long before they notice anything
# else about the edit. Single-pass: a two-pass measure/apply would double the
# render time for accuracy nobody can hear.
LOUDNESS = "loudnorm=I=-14:TP=-1.5:LRA=11"


def add_music_track(video_path: Path, music_path: Path, out_path: Path, music_volume: float = 0.85) -> None:
    """Attach a looped music track as the ONLY audio (for visual shorts)."""
    _run([
        "-i", str(video_path),
        "-stream_loop", "-1",
        "-i", str(music_path),
        "-filter_complex", f"[1:a]volume={music_volume},{LOUDNESS}[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_path),
    ])


def render_clip(
    source: Path,
    start: float,
    end: float,
    out_path: Path,
    ass_path: Path | None = None,
    width: int = 1080,
    height: int = 1920,
) -> None:
    """Cut [start, end] from creator footage: center-crop to the target
    aspect, captions burned in, ORIGINAL audio kept."""
    vf = _vf(width, height)
    if ass_path is not None:
        vf = f"{vf},ass={ass_path.name}:fontsdir=."
    _run(
        [
            "-ss", f"{start:.2f}",
            "-to", f"{end:.2f}",
            "-i", str(source),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            str(out_path),
        ],
        cwd=ass_path.parent if ass_path is not None else None,
    )


def image_to_clip(
    image: Path,
    duration: float,
    out_path: Path,
    width: int = 1080,
    height: int = 1920,
    zoom_in: bool = True,
    motion: str = "kenburns",
) -> None:
    """Turn a still into a moving shot (Ken Burns) so AI-generated scenes
    don't look like a slideshow.

    Alternating zoom direction between scenes keeps a long video from
    feeling mechanical — the caller flips zoom_in per index.
    """
    frames = max(2, int(round(max(0.5, duration) * 30)))
    # Oversample first: zoompan crops from the source, so a larger canvas
    # keeps the pan sharp instead of soft-scaling a 1080-wide image.
    big_w, big_h = width * 2, height * 2
    rate, ceiling = MOTION_CURVES.get(motion, MOTION_CURVES["kenburns"])
    if rate <= 0:
        z = "1"
    elif zoom_in:
        z = f"min(1+{rate}*on,{ceiling})"
    else:
        z = f"max({ceiling}-{rate}*on,1)"
    vf = (
        f"scale={big_w}:{big_h}:force_original_aspect_ratio=increase,"
        f"crop={big_w}:{big_h},"
        f"zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height},"
        "fps=30,format=yuv420p"
    )
    _run([
        "-loop", "1", "-i", str(image),
        "-t", f"{max(0.5, duration):.2f}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-an",
        str(out_path),
    ])


def cut_source(source: Path, start: float, duration: float, out_path: Path) -> None:
    """Cut a piece of creator footage for use as ONE segment's visual.

    Video only (narration/music own the soundtrack); scaling, cropping and
    looping happen later in render_segment*. If the requested start is past
    the end of the footage, the cut is pulled back so something plays."""
    total = probe_duration(source)
    start = max(0.0, min(start, max(0.0, total - 1.0)))
    _run([
        "-ss", f"{start:.2f}",
        "-t", f"{max(0.5, duration):.2f}",
        "-i", str(source),
        "-an",
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        str(out_path),
    ])


def mix_music(video_path: Path, music_path: Path, out_path: Path, music_volume: float = 0.12) -> None:
    """Loop background music under the narration, ducked to music_volume."""
    _run([
        "-i", str(video_path),
        "-stream_loop", "-1",
        "-i", str(music_path),
        "-filter_complex",
        # normalize=0 is NOT optional. ffmpeg's amix normalizes by default,
        # scaling every input by 1/n — so mixing narration with music quietly
        # threw away 6 dB of the narration on every single render, and the
        # "0.12" music bed was really playing at 0.06. Then loudnorm brings the
        # finished mix to a consistent target.
        f"[1:a]volume={music_volume}[m];"
        f"[0:a][m]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[mix];"
        f"[mix]{LOUDNESS}[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_path),
    ])


def concat_segments(segment_paths: list[Path], out_path: Path, workdir: Path) -> None:
    """Losslessly concat identically-encoded segment files."""
    list_file = workdir / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in segment_paths),
        encoding="utf-8",
    )
    _run([
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(out_path),
    ])


def probe_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {proc.stderr[-300:]}")
    return round(float(proc.stdout.strip()), 2)
