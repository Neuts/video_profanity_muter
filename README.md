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
