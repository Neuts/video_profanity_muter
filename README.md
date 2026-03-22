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

```bash
pip install faster-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

```

# Quick Start

Place mute_profanity.py and mute_profanity_gui.py in the same folder.
Run the GUI:Bashpython mute_profanity_gui.py
Select input video(s), output location, and desired options.
Click Start Processing.

Tip: Keep "Merge with built-in list" enabled and try Dialogue Enhancement + Beam Size 7 for best results.

### Main Options Explained


 - Whisper | Model large-v3 recommended for best accuracy
 - Beam Size | Higher = better detection, slower (5–10 is good balance)
 - Dialogue Enhancement | Applies filters to clean audio before transcription (often helps catch more)
 - Safe Mode | Uses subtitles to mute full sentences when Whisper misses profanity
 - Merge with built-in list | Combines your custom words with built-in list + variants
 - Verbose Logging | Shows full ffmpeg output (useful for debugging)


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


### Acknowledgments

Built on faster-whisper
Uses FFmpeg and MKVToolNix for audio/video processing


License
Free to use and modify for personal use.
