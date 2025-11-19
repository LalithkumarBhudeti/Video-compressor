import argparse
import subprocess
import sys
import os
from pathlib import Path



class VideoProcessor:
    def __init__(self, input_path, output_path, target_height=720, crf=24, preset='medium'):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.target_height = target_height
        self.crf = crf
        self.preset = preset

    def check_ffmpeg(self):
        """Verifies that FFmpeg is installed."""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: FFmpeg not found. Installing...")
            if IN_COLAB:
                subprocess.run("apt-get install ffmpeg", shell=True, check=True)
                return True
            return False

    def run_lanczos_pipeline(self):
        print(f"--- Starting Phase 1 Pipeline: Lanczos Downscale ({self.target_height}p) ---")
        
        scale_filter = f"scale=-2:{self.target_height}:flags=lanczos"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(self.input_path),
            "-vf", scale_filter,
            "-c:v", "libx265",      # Use H.265 Codec
            "-tag:v", "hvc1",       # <--- CRITICAL FIX FOR MAC/IPHONE PLAYBACK
            "-crf", str(self.crf),
            "-preset", self.preset,
            "-c:a", "copy",         # Keep original audio
            str(self.output_path)
        ]
        
        self._execute_ffmpeg(cmd)

    def _execute_ffmpeg(self, cmd):
        print(f"Running command: {' '.join(cmd)}")
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            for line in process.stdout:
                print(line, end='')
            process.wait()
            
            if process.returncode == 0:
                print(f"\n[SUCCESS] Video processed successfully.")
                self._print_stats()
            else:
                print("\n[ERROR] FFmpeg failed.")
        except Exception as e:
            print(f"Execution error: {e}")

    def _print_stats(self):
        if not self.output_path.exists():
            return
        orig_size = self.input_path.stat().st_size / (1024 * 1024)
        new_size = self.output_path.stat().st_size / (1024 * 1024)
        reduction = (1 - (new_size / orig_size)) * 100
        print(f"\n--- Stats ---")
        print(f"Original Size: {orig_size:.2f} MB")
        print(f"New Size:      {new_size:.2f} MB")
        print(f"Reduction:     {reduction:.2f}%")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--crf", type=int, default=24)
    
    args, unknown = parser.parse_known_args()

    input_filename = ""

    if IN_COLAB:
        print("Please upload your video file below:")
        uploaded = files.upload()
        
        if not uploaded:
            print("No file uploaded. Exiting.")
            return
            
        input_filename = list(uploaded.keys())[0]
        print(f"\nReceived: {input_filename}")
    else:
        if len(sys.argv) > 1:
            input_filename = sys.argv[1]
        else:
            print("Usage: python script.py input_video.mp4")
            return

    input_p = Path(input_filename)
    output_p = Path(f"mac_compatible_{args.height}p_{input_p.name}")

    processor = VideoProcessor(input_p, output_p, target_height=args.height, crf=args.crf)
    
    if processor.check_ffmpeg():
        processor.run_lanczos_pipeline()
        
        if IN_COLAB and output_p.exists():
            print("Downloading optimized video...")
            files.download(str(output_p))

if __name__ == "__main__":
    main()