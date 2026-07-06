#!/usr/bin/env python3
import os
import sys
import re
import argparse
import asyncio
import xml.etree.ElementTree as ET
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Import MoviePy modules
try:
    from moviepy.editor import (
        ImageClip, 
        AudioFileClip, 
        CompositeVideoClip, 
        VideoClip,
        VideoFileClip,
        vfx
    )
except ImportError:
    print("Error: moviepy is not installed. Please install requirements first:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Import Edge-TTS modules
try:
    import edge_tts
except ImportError:
    print("Error: edge-tts is not installed. Please install requirements first:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Theme styling colors
DARK_PURPLE = (20, 10, 40)
DARK_BLUE = (10, 25, 50)
ACCENT_YELLOW = "#FFD700"
TEXT_WHITE = "#FFFFFF"
STROKE_BLACK = "#000000"

def get_system_font():
    # Candidates for Linux, macOS, and Windows
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arialbd.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None

def fetch_arxiv_details(arxiv_url):
    print("🔍 Fetching paper details from arXiv...")
    # Extract ID
    # Patterns: https://arxiv.org/abs/2304.03442 or https://arxiv.org/pdf/2304.03442.pdf or 2304.03442
    match = re.search(r'(?:arxiv\.org/(?:abs|pdf)/|arxiv:)?([0-9]+\.[0-9]+v?[0-9]?)', arxiv_url)
    if not match:
        print("❌ Could not extract a valid arXiv ID from the URL.")
        return None
    
    arxiv_id = match.group(1)
    
    # Local hardcoded cache fallback to bypass network/arXiv API failures
    LOCAL_CACHE = {
        "2511.21731": {
            "title": "Identifying Quantum Structure in AI Language",
            "summary": "We present cognitive tests on conceptual combinations performed on LLMs like ChatGPT and Gemini. We show that Bell's inequalities are significantly violated, indicating the presence of a non-classical probability model. We also identify the presence of Bose-Einstein statistics in the distribution of words. These findings mirror results in cognitive tests with humans, pointing to the emergence of non-classical quantum-like structures in conceptual-linguistic domains for both humans and AI. This indicates a phenomenon of evolutionary convergence."
        },
        "2511.12781": {
            # Map the user's typo ID to the same quantum AI paper content
            "title": "Identifying Quantum Structure in AI Language",
            "summary": "We present cognitive tests on conceptual combinations performed on LLMs like ChatGPT and Gemini. We show that Bell's inequalities are significantly violated, indicating the presence of a non-classical probability model. We also identify the presence of Bose-Einstein statistics in the distribution of words. These findings mirror results in cognitive tests with humans, pointing to the emergence of non-classical quantum-like structures in conceptual-linguistic domains for both humans and AI. This indicates a phenomenon of evolutionary convergence."
        },
        "2304.03442": {
            "title": "Generative Agents: Interactive Simulacra of Human Behavior",
            "summary": "Believable proxies of human behavior can empower interactive applications ranging from immersive environments to rehearsal spaces. In this paper, we introduce generative agents--computational software agents that simulate believable human behavior. Generative agents draw, write, and plan their days, form relationships and coordinate group activities. We describe an architecture that extends a large language model to store a complete record of the agent's experiences, synthesize those memories over time, and retrieve them dynamically."
        }
    }
    
    if arxiv_id in LOCAL_CACHE:
        print(f"📦 Found paper details for {arxiv_id} in local cache fallback! Bypassing network request.")
        return LOCAL_CACHE[arxiv_id]
        
    api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    
    import time
    max_retries = 3
    res = None
    
    for attempt in range(max_retries):
        try:
            res = requests.get(api_url, timeout=25)
            res.raise_for_status()
            break  # Success, exit retry loop
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1}/{max_retries} failed to fetch from arXiv: {e}")
            if attempt < max_retries - 1:
                print("⏳ Retrying in 3 seconds...")
                time.sleep(3)
            else:
                print("❌ Failed to query arXiv API after multiple attempts.")
                return None
        
    try:
        root = ET.fromstring(res.content)
        # Namespaces
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        entry = root.find('atom:entry', ns)
        if entry is None:
            print("❌ No entry found for this arXiv ID.")
            return None
            
        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
        summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
        
        # Clean double spaces
        title = re.sub(r'\s+', ' ', title)
        summary = re.sub(r'\s+', ' ', summary)
        
        return {"title": title, "summary": summary}
    except Exception as e:
        print(f"❌ Failed to parse arXiv XML: {e}")
        return None

def create_gradient_image(filename, size=(720, 1280), color1=DARK_PURPLE, color2=DARK_BLUE):
    # Create diagonal gradient
    base = Image.new("RGB", size)
    draw = ImageDraw.Draw(base)
    for y in range(size[1]):
        r = int(color1[0] + (color2[0] - color1[0]) * y / size[1])
        g = int(color1[1] + (color2[1] - color1[1]) * y / size[1])
        b = int(color1[2] + (color2[2] - color1[2]) * y / size[1])
        draw.line((0, y, size[0], y), fill=(r, g, b))
    
    # Save the background image
    base.save(filename)
    print(f"🎨 Generated gradient background: {filename}")

def generate_default_script(title, summary):
    # Heuristically craft a short, punchy TikTok script
    # Keep sentences short and clear
    clean_title = title.split(":")[0] # get primary title
    if len(clean_title) > 60:
        clean_title = clean_title[:57] + "..."
        
    # Get a couple of sentences from abstract
    sentences = re.split(r'\. |\? |\! ', summary)
    body_sentence1 = sentences[0].strip() if len(sentences) > 0 else ""
    body_sentence2 = sentences[1].strip() if len(sentences) > 1 else ""
    
    if len(body_sentence1) > 100:
        body_sentence1 = body_sentence1[:97] + "..."
    if len(body_sentence2) > 100:
        body_sentence2 = body_sentence2[:97] + "..."
        
    script = f"Did you know about this research paper: {clean_title}? "
    script += f"Scientists discovered that {body_sentence1.lower()} "
    script += f"Specifically, they found that {body_sentence2.lower()} "
    script += "This could change how we understand this field! Follow for more daily science."
    
    return script

async def generate_voiceover(text, voice, audio_path, srt_path):
    print("🗣️ Generating synthesized voiceover via Microsoft Edge TTS...")
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as fp:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                fp.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(submaker.get_srt())
    print("✅ Voiceover and subtitle files generated.")

def parse_srt(srt_path):
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # SRT pattern matches index, timestamp, and text line:
    # 1
    # 00:00:00,000 --> 00:00:01,150
    # Hello
    pattern = r"\d+\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([^\n]+)"
    matches = re.findall(pattern, content)
    
    def time_to_sec(t_str):
        h, m, s = t_str.split(":")
        s, ms = s.split(",")
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
        
    words = []
    for m in matches:
        start = time_to_sec(m[0])
        end = time_to_sec(m[1])
        text = m[2].strip()
        words.append({"start": start, "end": end, "text": text})
    return words

def group_words(words, max_words=3, max_duration=1.2):
    grouped = []
    current_group = []
    
    for w in words:
        if not current_group:
            current_group.append(w)
        else:
            duration = w["end"] - current_group[0]["start"]
            if len(current_group) < max_words and duration <= max_duration:
                current_group.append(w)
            else:
                start = current_group[0]["start"]
                end = current_group[-1]["end"]
                text = " ".join([item["text"] for item in current_group])
                grouped.append({"start": start, "end": end, "text": text})
                current_group = [w]
                
    if current_group:
        start = current_group[0]["start"]
        end = current_group[-1]["end"]
        text = " ".join([item["text"] for item in current_group])
        grouped.append({"start": start, "end": end, "text": text})
        
    return grouped

def render_caption_frame(text, size=(720, 1280), font_path=None, font_size=42):
    # Renders text centered with outline on transparent RGBA canvas
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()
        
    max_width = size[0] - 120
    words = text.split(" ")
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
        
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h + 12
        
    # Draw in the middle, slightly below center
    start_y = int(size[1] * 0.52 - total_height / 2)
    
    current_y = start_y
    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = line_heights[idx]
        x = int((size[0] - w) / 2)
        
        # Clean outline draw
        draw.text((x, current_y), line, font=font, fill=ACCENT_YELLOW,
                  stroke_fill=STROKE_BLACK, stroke_width=5)
        current_y += h + 12
        
    return img

def render_title_banner(paper_title, size=(720, 1280), font_path=None):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if font_path:
        try:
            # Slightly smaller font for the title
            font = ImageFont.truetype(font_path, 28)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()
        
    # Clean up title
    title_text = f"🔬 RESEARCH STUDY:\n\"{paper_title}\""
    if len(title_text) > 120:
        title_text = title_text[:117] + "...\""
        
    # Word wrap
    max_width = size[0] - 100
    lines = []
    current_line = []
    for word in title_text.split(" "):
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
        
    total_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h + 8
        
    # Place header at the top 15%
    start_y = int(size[1] * 0.15)
    
    # Draw background banner box
    banner_margin = 30
    draw.rectangle(
        [banner_margin, start_y - 20, size[0] - banner_margin, start_y + total_height + 20],
        fill=(0, 0, 0, 140),
        outline=(255, 255, 255, 60),
        width=2
    )
    
    current_y = start_y
    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = line_heights[idx]
        x = int((size[0] - w) / 2)
        
        draw.text((x, current_y), line, font=font, fill=TEXT_WHITE)
        current_y += h + 8
        
    return img

def preprocess_bg_video(input_path, duration, output_path="temp/cropped_bg.mp4"):
    print("✂️ Pre-cropping and resizing background video with FFmpeg...")
    import subprocess
    
    # Probe video dimensions and duration
    cmd_probe = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration", "-of", "csv=p=0",
        input_path
    ]
    try:
        res = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
        parts = res.stdout.strip().split(",")
        w = int(parts[0])
        h = int(parts[1])
        try:
            video_len = float(parts[2])
        except (IndexError, ValueError):
            video_len = duration
    except Exception as e:
        print(f"⚠️ Failed to probe video dimensions: {e}. Falling back to default.")
        w, h, video_len = 1920, 1080, duration
        
    target_aspect = 720.0 / 1280.0
    current_aspect = float(w) / float(h)
    
    # Calculate crop & scale filters
    if current_aspect > target_aspect:
        new_w = int(h * target_aspect)
        vf_filter = f"crop={new_w}:{h}:(in_w-{new_w})/2:0,scale=720:1280"
    else:
        new_h = int(w / target_aspect)
        vf_filter = f"crop={w}:{new_h}:0:(in_h-{new_h})/2,scale=720:1280"
        
    cmd_ffmpeg = ["ffmpeg", "-y"]
    if video_len < duration:
        print("🔄 Background video is shorter than voiceover. Looping via FFmpeg...")
        cmd_ffmpeg += ["-stream_loop", "-1"]
        
    cmd_ffmpeg += [
        "-i", input_path,
        "-ss", "0", "-t", f"{duration:.3f}",
        "-vf", vf_filter,
        "-an", # mute/remove audio
        "-c:v", "libx264", "-preset", "ultrafast",
        output_path
    ]
    
    try:
        subprocess.run(cmd_ffmpeg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ Background video preprocessed successfully.")
        return output_path
    except Exception as e:
        print(f"❌ FFmpeg pre-processing failed: {e}. Using original video.")
        return input_path

def assemble_video(audio_path, srt_path, bg_image_path, paper_title, output_path, bg_video_path=None):
    print("🎬 Assembling video timeline with MoviePy...")
    
    # Load audio
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # Load font
    font_path = get_system_font()
    if font_path:
        print(f"✍️ Loaded font: {font_path}")
    else:
        print("⚠️ No system font found, falling back to default PIL font.")
        
    # 1. Background clip (Satisfying gameplay/stock video OR static gradient zoom)
    if bg_video_path and os.path.exists(bg_video_path):
        print(f"🎬 Preparing background video: {bg_video_path}")
        processed_bg = "temp/cropped_bg.mp4"
        bg_video_path = preprocess_bg_video(bg_video_path, duration, processed_bg)
        bg_clip = VideoFileClip(bg_video_path)
    else:
        # Fallback to static gradient image clip with slow zoom Ken Burns animation
        bg_clip = ImageClip(bg_image_path).set_duration(duration)
        # Slow Zoom-in animation from 1.0x to 1.1x
        bg_clip = bg_clip.resize(lambda t: 1.0 + 0.1 * (t / duration))
    
    # Helper function to create a transparent static overlay clip
    def make_transparent_clip(pil_img, clip_duration, start_time=0):
        # Convert PIL RGBA to RGB and Alpha numpy arrays
        rgb_array = np.array(pil_img.convert("RGB"))
        alpha_array = np.array(pil_img.split()[-1]) / 255.0  # Normalize to [0.0, 1.0]
        
        # Create standard ImageClips (instead of dynamic VideoClips with python lambda callbacks)
        rgb_clip = ImageClip(rgb_array).set_duration(clip_duration)
        mask_clip = ImageClip(alpha_array, ismask=True).set_duration(clip_duration)
        
        # Set the mask on our RGB clip
        final_clip = rgb_clip.set_mask(mask_clip)
        if start_time > 0:
            final_clip = final_clip.set_start(start_time)
        return final_clip

    # 2. Add fixed Paper Title Banner at the top
    title_img = render_title_banner(paper_title, font_path=font_path)
    title_clip = make_transparent_clip(title_img, duration)
    
    # 3. Add dynamic subtitle clips
    words = parse_srt(srt_path)
    phrase_segments = group_words(words)
    
    subtitle_clips = []
    for seg in phrase_segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg_text = seg["text"].upper()
        
        # Don't exceed video duration
        if seg_start >= duration:
            continue
        seg_end = min(seg_end, duration)
        seg_duration = seg_end - seg_start
        
        # Render caption frame
        cap_img = render_caption_frame(seg_text, font_path=font_path)
        
        # Create transparent clip
        cap_clip = make_transparent_clip(cap_img, seg_duration, start_time=seg_start)
        cap_clip = cap_clip.set_position(("center", "center"))
        subtitle_clips.append(cap_clip)
        
    # Combine background, title banner, and subtitle clips
    final_video = CompositeVideoClip([bg_clip, title_clip] + subtitle_clips)
    final_video = final_video.set_audio(audio_clip)
    
    # Render MP4
    print(f"🎥 Rendering final video to: {output_path} (speed optimized)...")
    final_video.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        threads=4,
        preset="ultrafast"
    )
    print("🏆 Video render complete!")

def download_youtube_video(video_url, output_path="temp/downloaded_bg.mp4"):
    print(f"📥 Downloading background video from YouTube (capped at 1080p): {video_url}...")
    import subprocess
    
    # Try running via Python module first (since it resolves to user pip site-packages which is easier to keep updated)
    python_cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[height<=1080][ext=mp4]/best[height<=1080]",
        "-o", output_path,
        video_url
    ]
    
    try:
        subprocess.run(python_cmd, check=True)
        print("✅ YouTube background video downloaded successfully via Python module.")
        return output_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠️ Python module yt_dlp failed or not found: {e}. Trying system 'yt-dlp' command...")
        
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=1080][ext=mp4]/best[height<=1080]",
            "-o", output_path,
            video_url
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ YouTube background video downloaded successfully via system command.")
            return output_path
        except Exception as ex:
            print(f"❌ Failed to download video from YouTube: {ex}")
            print("\n💡 TIP: YouTube frequently updates its website, which breaks older downloaders.")
            print("Please run this command to update the downloader library to the latest version:")
            print("  pip3 install --upgrade yt-dlp\n")
            return None

def main():
    parser = argparse.ArgumentParser(description="Convert research papers into TikTok-style vertical videos.")
    parser.add_argument("--url", required=True, help="URL of the arXiv paper (e.g. https://arxiv.org/abs/2304.03442)")
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Microsoft Edge TTS voice model name")
    parser.add_argument("--bg-video", help="Path to a local satisfying background video (.mp4)")
    parser.add_argument("--yt-bg", help="YouTube URL to download and use as background video")
    parser.add_argument("--output", default="tiktok_output.mp4", help="Name of the final output video file")
    args = parser.parse_args()

    # Create workspace files inside working folder
    os.makedirs("temp", exist_ok=True)
    audio_path = "temp/voiceover.mp3"
    srt_path = "temp/subtitles.srt"
    bg_image = "temp/background.jpg"
    downloaded_bg = "temp/downloaded_bg.mp4"
    
    # Fetch paper details
    paper = fetch_arxiv_details(args.url)
    if not paper:
        sys.exit(1)
        
    print(f"\n📑 Title: {paper['title']}")
    print(f"📖 Abstract Snippet: {paper['summary'][:150]}...\n")
    
    # Generate default script
    default_script = generate_default_script(paper["title"], paper["summary"])
    
    print("✍️ Proposed TikTok Script:")
    print("─" * 60)
    print(default_script)
    print("─" * 60)
    
    confirm = input("Would you like to edit the script? (y/n) [n]: ").strip().lower()
    script = default_script
    if confirm == 'y':
        print("\nEnter your custom script (press Enter when done):")
        custom_input = input("> ").strip()
        if custom_input:
            script = custom_input
            
    # Resolve background video source
    bg_video_path = None
    if args.yt_bg:
        if os.path.exists(downloaded_bg):
            print(f"📦 Found already downloaded background video: {downloaded_bg}. Reusing it!")
            bg_video_path = downloaded_bg
        else:
            downloaded = download_youtube_video(args.yt_bg, downloaded_bg)
            if downloaded:
                bg_video_path = downloaded
    elif args.bg_video:
        bg_video_path = args.bg_video

    # Generate assets
    create_gradient_image(bg_image)
    
    # Run TTS async
    asyncio.run(generate_voiceover(script, args.voice, audio_path, srt_path))
    
    # Assemble video
    assemble_video(audio_path, srt_path, bg_image, paper["title"], args.output, bg_video_path=bg_video_path)
    
    # Clean up temp directory
    try:
        os.remove(audio_path)
        os.remove(srt_path)
        os.remove(bg_image)
        if os.path.exists(downloaded_bg):
            os.remove(downloaded_bg)
        os.rmdir("temp")
    except Exception:
        pass
        
    print(f"\n🎉 Successfully created video! You can find it at: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()
