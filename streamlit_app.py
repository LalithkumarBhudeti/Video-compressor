#!/usr/bin/env python3

from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, List

# Streamlit detection (optional)
try:
    import streamlit as st  # type: ignore
    USING_STREAMLIT = True
except Exception:
    USING_STREAMLIT = False

VERSION = "1.2"

# ------------------------------
# Utility / FFmpeg command builders
# ------------------------------
def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None

def build_ffmpeg_cmd(
    infile: Path,
    outfile: Path,
    target_height: int = 720,
    crf: int = 24,
    preset: str = "medium",
    reencode_audio: bool = False,
    codec: str = "libx265",
) -> List[str]:
    """Return ffmpeg command list for downscaling using lanczos + codec."""
    scale_filter = f"scale=-2:{target_height}:flags=lanczos"
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(infile),
        "-vf", scale_filter,
        "-c:v", codec,
    ]
    # Keep mac/iphone-friendly tag for h265 outputs
    if codec == "libx265":
        cmd += ["-tag:v", "hvc1"]
    cmd += ["-crf", str(crf), "-preset", preset]
    if reencode_audio:
        cmd += ["-c:a", "aac", "-b:a", "128k"]
    else:
        cmd += ["-c:a", "copy"]
    cmd.append(str(outfile))
    return cmd

def run_subprocess_and_stream(cmd: List[str], output_callback=None) -> int:
    """
    Execute subprocess, stream lines to output_callback (if provided).
    output_callback should accept a single string argument (one line or a chunk).
    """
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        assert proc.stdout is not None
        buffer: List[str] = []
        for line in proc.stdout:
            buffer.append(line)
            # throttle UI updates a bit by keeping only last N lines to show
            if len(buffer) > 400:
                buffer = buffer[-400:]
            if output_callback:
                output_callback("".join(buffer))
        proc.wait()
        return proc.returncode
    except FileNotFoundError:
        if output_callback:
            output_callback("ffmpeg executable not found.")
        return 127
    except Exception as exc:
        if output_callback:
            output_callback(f"Error running ffmpeg: {exc}")
        return 1

def print_stats(infile: Path, outfile: Path, output_func=print) -> None:
    if not infile.exists():
        output_func(f"Original file missing: {infile}")
        return
    if not outfile.exists():
        output_func(f"Output file not found: {outfile}")
        return
    orig_mb = infile.stat().st_size / (1024 * 1024)
    new_mb = outfile.stat().st_size / (1024 * 1024)
    reduction_pct = (1 - (new_mb / orig_mb)) * 100 if orig_mb > 0 else 0
    output_func("\n--- Stats ---")
    output_func(f"Original Size: {orig_mb:.2f} MB")
    output_func(f"New Size:      {new_mb:.2f} MB")
    output_func(f"Reduction:     {reduction_pct:.2f} %")

# ------------------------------
# Core compress function
# ------------------------------
def compress_video(
    infile: Path,
    outfile: Path,
    height: int = 720,
    crf: int = 24,
    preset: str = "medium",
    reencode_audio: bool = False,
    codec: str = "libx265",
    log_callback=None,
) -> int:
    cmd = build_ffmpeg_cmd(infile, outfile, target_height=height, crf=crf, preset=preset, reencode_audio=reencode_audio, codec=codec)
    if log_callback:
        return run_subprocess_and_stream(cmd, output_callback=log_callback)
    else:
        return run_subprocess_and_stream(cmd, output_callback=print)

# ------------------------------
# Streamlit UI
# ------------------------------
def streamlit_app_ui() -> None:
    st.set_page_config(page_title="Video Compressor", layout="centered")
    st.title("Video Compressor — Lanczos downscale + x265 (H.265)")
    st.caption("Use the sidebar to choose resolution and quality. To increase upload limit change ~/.streamlit/config.toml")

    st.sidebar.header("Settings")

    # Preset selector with Custom option
    preset_map = {
        "144p": 144,
        "360p": 360,
        "480p": 480,
        "720p": 720,
        "1080p": 1080,
        "Custom": "custom",
    }
    preset_choice = st.sidebar.selectbox("Target resolution", options=list(preset_map.keys()), index=3)
    if preset_map[preset_choice] == "custom":
        height = st.sidebar.number_input("Custom height (px)", min_value=64, max_value=4320, value=720, step=1)
    else:
        height = int(preset_map[preset_choice])

    crf = st.sidebar.slider("CRF (quality, lower = better)", min_value=0, max_value=51, value=24)
    x265_preset = st.sidebar.selectbox("x265 preset", ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"], index=5)
    reencode_audio = st.sidebar.checkbox("Re-encode audio to AAC (safer)", value=False)
    codec = st.sidebar.selectbox("Video codec", ["libx265", "libx264"], index=0)
    st.sidebar.markdown("---")
    st.sidebar.markdown("Tip: For mac/iPhone playback use libx265 (H.265). If you need maximum compatibility, use libx264.")

    st.markdown("### Upload video (supported: MP4, MOV, MKV, M4V, HEVC, AVI, MPEG4).")
    uploaded = st.file_uploader("Choose a video", type=["mp4", "mov", "mkv", "m4v", "hevc", "avi", "mpeg4"])

    cols = st.columns([2, 1])
    with cols[0]:
        out_name = st.text_input("Output filename (optional)", value="")
    with cols[1]:
        run_button = st.button("Start compression")

    if not is_ffmpeg_available():
        st.warning("ffmpeg not found on PATH. Install it (e.g., `brew install ffmpeg`) and restart the app.")
    else:
        st.success("ffmpeg found on PATH.")

    output_area = st.empty()  # will show logs
    preview_area = st.empty()

    if run_button:
        if uploaded is None:
            st.error("Please upload a file first.")
        else:
            # Write uploaded file to a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
                tmp_path = Path(tmp.name)
                tmp.write(uploaded.getbuffer())
                tmp.flush()

            input_path = tmp_path
            # prepare output path in cwd to allow download easily
            output_filename = out_name.strip() or f"mac_compatible_{height}p_{Path(uploaded.name).name}"
            output_path = Path.cwd() / output_filename

            st.info(f"Processing `{uploaded.name}` → `{output_path.name}` at {height}p using {codec}")
            # show input preview if possible
            try:
                preview_area.video(str(input_path))
            except Exception:
                pass

            # run ffmpeg and stream logs
            def write_logs(t: str):
                # write small chunks to Streamlit area
                output_area.text(t)

            with st.spinner("Running ffmpeg — this may take a while depending on video size and CPU"):
                rc = compress_video(
                    infile=input_path,
                    outfile=output_path,
                    height=height,
                    crf=crf,
                    preset=x265_preset,
                    reencode_audio=reencode_audio,
                    codec=codec,
                    log_callback=write_logs,
                )

            if rc == 0:
                st.success("Compression finished successfully!")
                print_stats(input_path, output_path, lambda s: output_area.text(s) if isinstance(s, str) else output_area.text(str(s)))
                try:
                    preview_area.video(str(output_path))
                except Exception:
                    pass
                # Provide download button
                with open(output_path, "rb") as f:
                    st.download_button("Download compressed video", data=f, file_name=output_path.name, mime="video/mp4")
            else:
                st.error(f"ffmpeg failed with code {rc}. Check logs above.")

            # cleanup input temp file (keep output)
            try:
                input_path.unlink()
            except Exception:
                pass

# ------------------------------
# CLI / main
# ------------------------------
def run_cli_mode(args) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file does not exist: {input_path}")
        return 3

    output_path = Path(args.output) if args.output else input_path.parent / f"mac_compatible_{args.height}p_{input_path.name}"

    if not is_ffmpeg_available():
        print("ffmpeg not found on PATH. Install it on mac: brew install ffmpeg")
        return 4

    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    rc = compress_video(
        infile=input_path,
        outfile=output_path,
        height=args.height,
        crf=args.crf,
        preset=args.preset,
        reencode_audio=args.reencode_audio,
        codec=args.codec,
        log_callback=None,
    )
    if rc == 0:
        print("\n[SUCCESS] ffmpeg finished successfully.")
        print_stats(input_path, output_path, print)
    else:
        print(f"\n[ERROR] ffmpeg exited with return code: {rc}")
        print("Tip: If ffmpeg failed due to audio codec copy errors, re-run with --reencode-audio.")
    return rc

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Video compressor (streamlit-capable).")
    p.add_argument("--version", action="version", version=VERSION)
    p.add_argument("--input", "-i", type=str, help="Input video file path (CLI mode).")
    p.add_argument("--output", "-o", type=str, help="Output video path (CLI mode).")
    p.add_argument("--height", type=int, default=720, help="Target height in pixels (CLI).")
    p.add_argument("--crf", type=int, default=24, help="CRF quality (x265).")
    p.add_argument("--preset", type=str, default="medium", help="x265 preset.")
    p.add_argument("--reencode-audio", action="store_true", help="If set, audio will be re-encoded to AAC.")
    p.add_argument("--codec", type=str, default="libx265", choices=["libx265", "libx264"], help="Video codec to use (CLI).")
    return p.parse_args(argv)

def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    # If Streamlit is running, call UI function
    # Best-effort detect streamlit context:
    if USING_STREAMLIT and ("streamlit" in " ".join(sys.argv).lower()):
        try:
            streamlit_app_ui()
            return 0
        except Exception as e:
            print("Streamlit UI failed, falling back to CLI. Error:", e)

    # CLI mode
    if args.input:
        return run_cli_mode(args)

    # No UI and no CLI input: print help
    print("No Streamlit UI detected and no CLI input provided. To use Streamlit UI run:")
    print("    streamlit run streamlit_video_compressor.py")
    print("To use CLI mode:")
    print("    python streamlit_video_compressor.py --input input.mp4 --height 720 --crf 24")
    return 0

if __name__ == "__main__":
    sys.exit(main())
