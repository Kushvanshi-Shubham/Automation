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

VF = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"


def _run(args: list[str]) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode != 0:
        logger.error("ffmpeg failed: %s", proc.stderr[-2000:])
        raise RuntimeError(f"ffmpeg failed: {proc.stderr[-500:]}")


def render_segment(clip_path: Path, audio_path: Path, duration: float, out_path: Path) -> None:
    """Video looped/trimmed to narration duration, 9:16, with segment audio."""
    _run([
        "-stream_loop", "-1",
        "-i", str(clip_path),
        "-i", str(audio_path),
        "-t", f"{duration + 0.15:.2f}",  # small tail so audio never clips
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", VF,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
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
