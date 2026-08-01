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
) -> None:
    """Video looped/trimmed to narration duration, 9:16, with segment audio
    and optional burned-in captions."""
    vf = VF
    if ass_path is not None:
        # Run with cwd = the ASS file's directory and reference it by bare
        # filename — sidesteps Windows drive-letter escaping in filter args.
        vf = f"{VF},ass={ass_path.name}"
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
) -> None:
    """Visual-only segment: no narration track (music is added after concat)."""
    vf = VF
    if ass_path is not None:
        vf = f"{VF},ass={ass_path.name}"
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


def add_music_track(video_path: Path, music_path: Path, out_path: Path, music_volume: float = 0.85) -> None:
    """Attach a looped music track as the ONLY audio (for visual shorts)."""
    _run([
        "-i", str(video_path),
        "-stream_loop", "-1",
        "-i", str(music_path),
        "-filter_complex", f"[1:a]volume={music_volume}[a]",
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
) -> None:
    """Cut [start, end] from creator footage: 9:16 center-crop, captions
    burned in, ORIGINAL audio kept (that's the point of creator clips)."""
    vf = VF
    if ass_path is not None:
        vf = f"{VF},ass={ass_path.name}"
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


def mix_music(video_path: Path, music_path: Path, out_path: Path, music_volume: float = 0.12) -> None:
    """Loop background music under the narration, ducked to music_volume."""
    _run([
        "-i", str(video_path),
        "-stream_loop", "-1",
        "-i", str(music_path),
        "-filter_complex",
        f"[1:a]volume={music_volume}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
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
