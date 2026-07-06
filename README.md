# 🎓 Scholar-to-TikTok Video Generator

An automated short-form video generator designed to transform academic research papers into engaging, high-retention TikTok, YouTube Shorts, and Instagram Reels videos. The pipeline pulls paper details, synthesizes voiceovers, fetches high-quality background video clips (like Minecraft parkour), and renders everything together with synchronized captions.

<p align="center">
  <img src="sample.gif" width="240" alt="Scholar-to-TikTok Demo">
</p>


---

## ✨ Features

- **Robust arXiv Fetching:** Directly queries the arXiv API over HTTPS with automated 3-attempt retry logic and connection timeouts.
- **Offline Cache Fallback:** Hardcoded metadata database for popular academic papers to enable testing without network requests.
- **High-Quality TTS:** Generates synthesized speech using Microsoft Edge TTS with precise word-boundary subtitle tracking.
- **FFmpeg Pre-processing:** Crops, center-aligns, scales to 9:16 (`720x1280`), loops, and strips audio from background videos using optimized FFmpeg commands in less than a second.
- **Accelerated Compositing:** Uses cached static `ImageClip` overlays and multi-threaded rendering (GIL bypass) to render short videos in **under 45 seconds** (600% speedup).
- **YouTube Downloader:** Integrates `yt-dlp` to download background clips directly from YouTube, capped at 1080p.

---

## 🛠️ Installation

### 1. System Dependencies
You must have **FFmpeg** installed on your system to process video and audio:
```bash
# Linux (Ubuntu/Debian)
sudo apt update && sudo apt install -y ffmpeg
```

### 2. Python Setup
Clone the repository and install the required dependencies:
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

Run the generator by passing an arXiv URL and a YouTube background video link:

```bash
./generate_video.py --url https://arxiv.org/abs/2511.12781 --yt-bg "https://www.youtube.com/watch?v=XBIaqOm0RKQ"
```

### ⚙️ Command-Line Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--url` | **(Required)** The arXiv abstract page URL | None |
| `--yt-bg` | YouTube video URL to use as gameplay background | None |
| `--voice` | Microsoft Edge TTS voice model | `en-US-ChristopherNeural` |
| `--output` | Output filename path | `tiktok_output.mp4` |
| `--bg-video` | Local path to pre-downloaded background video | None |

---

## 📂 Project Structure

```text
├── generate_video.py   # Main video generation logic & CLI interface
├── requirements.txt    # Python dependencies
├── .gitignore          # Excludes media, cache, and virtual environments
└── README.md           # Documentation
```

---

## 🎨 Customizing the Design
To change font family, color, font-sizes, or layout options, modify the configuration variables at the top of `generate_video.py`:
- **Subtitles:** Centered word/phrase captions styled in bright yellow with custom black outline stroke width.
- **Title Block:** Semitransparent slate header card at the top displaying the research study name.
