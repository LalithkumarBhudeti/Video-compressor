# 📹 Video Compressor — Streamlit + FFmpeg (H.265)

A powerful, easy-to-use **video compression and downscaling tool** built with **Streamlit** and **FFmpeg**.
Compress high-resolution videos into lighter, streaming-friendly formats using **Lanczos downscaling** and **H.265 (HEVC)** encoding — all through a clean web interface.

Perfect for:

* Reducing huge mobile videos
* Creating YouTube/TikTok/Instagram-friendly variants
* Low-bandwidth sharing
* Research pipelines (baseline before neural downscaling)
* Generating multi-resolution datasets

---

## 🚀 Features

### 🎛️ Streamlit Web Interface

Interactive UI to upload videos, choose compression settings, preview results, and download output.

### 🖼️ Resolution Presets

Choose from common streaming formats:

* **144p**
* **360p**
* **480p**
* **720p**
* **1080p**
* **Custom height**

### 🎚️ CRF-Based Quality Control

Select your preferred quality using Constant Rate Factor (CRF).
Lower = better quality (and larger files).

### 🎞️ High-Quality Lanczos Downscaling

Includes:

```
scale=-2:<height>:flags=lanczos
```

Provides crisp resizing with minimal artifacts.

### 🎥 H.265 (libx265) Encoding

Delivers excellent compression efficiency.
Includes:

```
-tag:v hvc1
```

for full **Mac/iPhone compatibility**.

### 🎥 Optional H.264 Support

Use `libx264` for maximum compatibility across older devices.

### 🔊 Audio Options

* Copy original audio track
* Or re-encode to AAC at 128 kbps

### 📝 Live FFmpeg Logs

FFmpeg progress is streamed directly in the UI for transparency and debugging.

### 🖥️ CLI Support

Use the tool without Streamlit:

```bash
python streamlit_video_compressor.py -i input.mp4 --height 720 --crf 24
```

---

## 🛠️ Tech Stack

* **Python 3**
* **Streamlit**
* **FFmpeg**
* **subprocess**
* **pathlib**
* **tempfile**

---

## 📦 Installation

### 1️⃣ Install Python packages

```bash
pip install streamlit
```

### 2️⃣ Install FFmpeg

**macOS (Homebrew):**

```bash
brew install ffmpeg
```

**Ubuntu:**

```bash
sudo apt install ffmpeg
```

**Windows:**
Download from: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

---

## ▶️ Running the Application

Run the Streamlit app:

```bash
streamlit run streamlit_video_compressor.py
```

Then open the browser link (typically `http://localhost:8501`).

---

## 🧪 Example FFmpeg Command

Here’s what the tool executes behind the scenes:

```bash
ffmpeg -i input.mp4 \
  -vf scale=-2:720:flags=lanczos \
  -c:v libx265 -tag:v hvc1 \
  -crf 24 -preset medium \
  -c:a copy \
  output.mp4
```

---

## 📂 Folder Structure

```
/
├── streamlit_video_compressor.py     # Main application file
├── README.md                         # Project documentation
└── sample_videos/                    # (Optional) test videos
```

---

## 🔮 Roadmap

* [ ] Neural downscaling integration (ProgDownLite / SuperRes)
* [ ] Batch processing mode
* [ ] Multi-resolution output generation
* [ ] GPU-accelerated encoding
* [ ] Cloud deployment (Streamlit Cloud / HuggingFace Spaces)
* [ ] Mobile-responsive UI

---

## 🤝 Contributing

Pull requests are welcome!
If you’d like to request a feature or report a bug, open an issue in the repo.

---

## ⭐ Support

If you found this tool useful, consider giving the repository a **Star ⭐**!

