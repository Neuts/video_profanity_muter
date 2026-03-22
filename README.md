# Profanity Muter

**A local, offline AI-powered tool to automatically mute profanity in videos while preserving original length and timing.**

Built with faster-whisper + FFmpeg. Runs entirely on your machine — no data leaves your computer.

---

### Features

- **Accurate profanity detection** using Whisper (large-v3 recommended)
- **Preserves full video length** — only mutes audio, no cutting
- **Safe Mode** — catches profanities Whisper misses by using subtitle data
- **Dialogue Enhancement** — optional audio cleanup to improve detection on noisy tracks
- **Custom word lists** — load your own `.txt` file (supports phrases)
- **Smart merging** — combine custom list with built-in words + common variants (f*ck, sh*t, a$$, etc.)
- **Adjustable Beam Size** — trade speed for accuracy (1–15)
- **Native Desktop GUI** with live log, progress bar, and cancel button
- **Batch processing** support
- **VLC compatibility fix** (timestamp cleaning)
- **Quiet mode** — clean logs by default (reduces Windows crashes)

---

### Requirements

- Python 3.9+
- FFmpeg (must be in PATH)
- MKVToolNix (`mkvmerge` must be in PATH — required for .mkv files)
- GPU recommended (CUDA) for best performance


---

### Setup Guide (Recommended: Using Virtual Environment)

#### 1. Clone or Download the Project
Download or clone the project folder containing:
- `mute_profanity.py`
- `mute_profanity_gui.py`
- `README.md`




#### 2. Create a Virtual Environment

Open a terminal / command prompt in the project folder and run:

```bash
# Create virtual environment
python -m venv venv

# Activate the virtual environment

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate


```

### 3. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install required packages
pip install faster-whisper torch torchvision torchaudio

# For NVIDIA GPU users (CUDA 12.8 recommended):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

### 4. Install System Dependencies


FFmpeg: Download from https://ffmpeg.org/download.html or use your package manager (winget install ffmpeg, apt install ffmpeg, etc.)
MKVToolNix: Download from https://mkvtoolnix.download/ (make sure mkvmerge is in your PATH)



# Quick Start

Place mute_profanity.py and mute_profanity_gui.py in the same folder.
Run the GUI:Bashpython mute_profanity_gui.py
Select input video(s), output location, and desired options.
Click Start Processing.

Tip: Keep "Merge with built-in list" enabled and try Dialogue Enhancement + Beam Size 7 for best results.

Run gui.bat for windows clients, it will load a fully featured GUI with all of the options included in this script.

### Main Options Explained


 - **Whisper | Model large-v3 recommended for best accuracy
 - **Beam Size | Higher = better detection, slower (5–10 is good balance)
 - **Dialogue Enhancement | Applies filters to clean audio before transcription (often helps catch more)
 - **Safe Mode | Uses subtitles to mute full sentences when Whisper misses profanity
 - **Merge with built-in list | Combines your custom words with built-in list + variants
 - **Verbose Logging | Shows full ffmpeg output (useful for debugging)


### Custom Word List Format
Create a plain text file (custom.txt) with one word or phrase per line:
txt# My custom triggers
idiot
bloody hell
for fuck's sake
mf
You can leave "Merge with built-in list" checked to combine it with the default words.



Project Status
Current Version: 1.0 Stable
Last Updated: March 22, 2026
Both scripts are marked stable and ready for regular use.

### Known Limitations

Cannot achieve 100% detection due to limitations of local Whisper models
Mutes (silence) rather than replacing with bleeps or cutting
Performance depends on your hardware (GPU strongly recommended for large-v3)

---
### Troubleshooting
Common Issues & Solutions
1. "mute_profanity.py not found" error

Make sure both mute_profanity.py and mute_profanity_gui.py are in the same folder.
Run the GUI from that folder.

2. FFmpeg or mkvmerge "command not found"

Ensure FFmpeg and MKVToolNix are installed and added to your system PATH.
Restart your terminal / computer after installing.

3. Process exits with code 3221226505 (Windows only)

This is usually caused by large output from ffmpeg.
Solution: Keep Verbose logging unchecked (uses --quiet mode).
Try enabling Dialogue Enhancement — it often reduces output noise.

4. Whisper crashes or runs out of memory

Use a smaller model (medium or large-v2 instead of large-v3)
Lower Beam Size to 5
Close other GPU-heavy applications
Disable Dialogue Enhancement temporarily

5. Very few or no profanities detected

Try enabling Dialogue Enhancement
Increase Beam Size to 7 or 10
Use large-v3 model
Check your custom word list and ensure "Merge with built-in list" is enabled

6. Safe Mode not adding any blocks

Make sure your video has English subtitles
Enable Validate to see the comparison numbers
Try a higher Beam Size or enable Dialogue Enhancement

7. GUI looks broken or buttons are misaligned

Try switching Dark Mode on/off
Resize the window slightly

8. Slow processing

Use distil-large-v3 or large-v3-turbo for faster speed (slightly lower accuracy)
Lower Beam Size
Disable Dialogue Enhancement

9. Custom word list not working

Make sure the file is plain text (.txt)
One word or phrase per line
Lines starting with # are treated as comments

10. Temp files not cleaning up

This is normal if the program crashes. You can safely delete any temp_audio_*.flac or temp_subs_*.srt files manually.

---

### Acknowledgments

Built on faster-whisper
Uses FFmpeg and MKVToolNix for audio/video processing


License
Free to use and modify for personal use.
